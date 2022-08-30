import os
from pprint import pprint

from deta import Deta
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sentry_sdk import init

from config import Config

# from newrelic.agent import initialize


print("initializing app and extensions...", end="")
app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)  # TODO: add rate limit
print("done")

# from sentry_sdk.integrations.flask import FlaskIntegration
# from sentry_sdk.integrations.httpx import HttpxIntegration

# print("initiating analytics...", end="")
# initialize(os.path.join(app.config["ROOT_DIR"], "newrelic.ini"))
# init(
#     dsn=app.config["SENTRY_SDK_DSN"],
#     integrations=[FlaskIntegration(), HttpxIntegration()],
#     traces_sample_rate=1.0,
# )
# print("done")
from re import sub
from unicodedata import normalize

print("defining helper functions...", end="")


def condense_args(request, lower=False):
    inbound = {}
    try:
        inbound = request.get_json(force=True)
    except:
        pass
    inbound.update(dict(**request.args))
    return {k.lower(): v for k, v in inbound.items()} if lower else inbound


def readify(text):
    return sub(" +", " ", normalize("NFKD", text).replace("\n", "")).strip()


print("done")

from .start.locations import scrape_locations
from .start.menus import scrape_menus

print("scraping locations and menus...", end="")
deta = Deta(app.config["DETA_KEY"])
foodDB = deta.Base("food")
foodDB.put(scrape_locations(), "locations")
foodDB.put(scrape_menus(), "menus")
print("done")

# TODO: get quarter end dates for current quarter
# print("scraping calendar...")
# page = get('https://registrar.ucsc.edu/calendar/future.html')
# soup = BeautifulSoup(page.text, 'lxml', SoupStrainer(['h3', 'td']))
# print(soup)

from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from httpx import get

print("scraping pisa headers...", end="")
last, store, comp = (
    "",
    [],
    {"action": {"action": ["results", "detail"]}},  # next is adjusted by page
)
page = get("https://pisa.ucsc.edu/class_search/index.php")
soup = BeautifulSoup(
    page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
)
# TODO: try to find a way to capture outbound headers of a requested url's post request
# FIXME: GE top level key has weird escape chars
for i in soup:
    if i.name == "label":
        snake = sub(r"(_|-)+", " ", i.text.strip()).title().replace(" ", "")
        camel = snake[0].lower() + snake[1:]
        if i.get("class") == ["col-sm-2", "form-control-label"]:
            comp[camel], last = {}, camel
        elif i.get("class") == ["sr-only"]:
            comp[last]["input"] = ""
        elif i.find("input"):
            comp[camel] = {i.find("input")["name"]: i.find("input")["value"]}
    elif i.name == "select":
        options = {}
        for j in i:
            if isinstance(j, NavigableString):
                continue
            options[j["value"]] = j.text
        comp[last][i["name"]] = options
        if "input" in comp[last]:
            del comp[last]["input"]
            store.append(last)
    elif i.name == "input":
        if i.get("type") == "text":
            comp[store[-1]][i["name"]] = ""
# fill empty items with the last element of the last item
last = ""
for i in comp:
    if len(comp[i]) == 0:
        transfer = [list(comp[last].keys())[-1], list(comp[last].values())[-1]]
        del comp[last][transfer[0]]
        comp[i][transfer[0]] = transfer[1]
    last = i
print("done")
print("building catalog headers...", end="")
template = {}
for i in comp:
    if len(comp[i]) != 1:
        template[i] = {}
        for j in comp[i]:
            if j[:-1].split("_")[-1] == "op":
                template[i]["operation"] = comp[i][j]
            elif j[:-1].split("_")[-1] == "nbr" or "_" not in j:
                template[i]["value"] = comp[i][j]
            else:
                template[i][j[:-1].split("_")[-1]] = comp[i][j]
    else:
        template[i] = comp[i][list(comp[i].keys())[0]]
modes = {}
for i in list(template.keys())[-4:]:
    modes[i] = True
    del template[i]
template = template | {"instructionModes": modes}
template["page"], outbound = {"number": 1, "results": 25}, {}
for i in comp:
    for j in comp[i]:
        if isinstance(comp[i][j], dict):
            outbound[j] = list(comp[i][j].keys())[0]
        elif isinstance(comp[i][j], list):
            outbound[j] = comp[i][j][0]
        else:
            outbound[j] = comp[i][j]
# TODO: adjust rec_dur
outbound["rec_start"], outbound["rec_dur"] = "0", "25"
if len(template) == 2:
    template, outbound = None, None
# catalogDB = deta.Base("catalog")
# catalogDB.put(template, "template")
# catalogDB.put(outbound, "outbound")
print("error")

# from orjson import OPT_INDENT_2
# print("generating test headers...", end="")
# test = {}
# for i in template:
#     if isinstance(template[i], dict):
#         test[i] = list(template[i].keys())[0]
#     elif isinstance(template[i], list):
#         test[i] = template[i][0]
#     else:
#         test[i] = template[i]
# with open("testing/main.json", "wb") as f:
#     f.write(dumps(test, option=OPT_INDENT_2))
# print("done")

# print("converting json to form-data...", end="")
# s = ""
# for i in outbound:
#     s += f"{i}: {outbound[i]}\n"
# with open ("testing/main.txt", "w") as f:
#     f.write(s)
# print("done")


print("done")

from app import errors
from app.catalog import catalog
from app.food import food
from app.home import home
from app.laundry import laundry

print("registering blueprints...", end="")
app.register_blueprint(home)
app.register_blueprint(food, url_prefix="/food")
app.register_blueprint(laundry, url_prefix="/laundry")
app.register_blueprint(catalog, url_prefix="/catalog")
# metro endpoint: https://www.scmtd.com/en/routes/schedule
# app.register_blueprint(catalog.catalog_bp, url_prefix="/metro")
# TODO: maybe an instructional calender blueprint?
print("done")
