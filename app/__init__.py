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
# set up limits
limiter = Limiter(app, key_func=get_remote_address)  # TODO: add rate limit
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
from re import findall
from re import sub
from unicodedata import normalize

print("defining helper functions...", end="")


# TODO: remove lower option, conserve strict inbound header case sensitivity
def camel_case(text):
    snake = sub(r"(_|-)+", " ", text).title().replace(" ", "")
    return snake[0].lower() + snake[1:]


def condense_args(request, lower=False):
    inbound = {}
    try:
        inbound = request.get_json(force=True)
    except:
        pass
    inbound.update(dict(request.args))  # TODO: figure out "**" operators
    return {k.lower(): v for k, v in inbound.items()} if lower else inbound


def force_to_int(text):
    if any([c.isdigit() for c in text]):
        return int(sub(r"\D", "", text))
    return text


def parse_days_times(text):
    text = text.split(" ")
    days = {
        "M": "Monday",
        "Tu": "Tuesday",
        "W": "Wednesday",
        "Th": "Thursday",
        "F": "Friday",
    }
    acros, times = findall("[A-Z][^A-Z]*", text[0]), text[1].split("-")
    {"start": times[0], "end": times[1]}
    return {
        "days": {i: days[i] for i in acros},
        "times": {"start": times[0], "end": times[1]},
    }


def readify(text):
    return sub(" +", " ", normalize("NFKD", text).replace("\n", "")).strip()


print("done")

from .start.locations import scrape_locations
from .start.menus import scrape_menus

print("scraping food data...", end="")
deta = Deta(app.config["DETA_KEY"])
foodDB = deta.Base("food")
foodDB.put(scrape_locations(), "locations")
foodDB.put(scrape_menus(), "menus")
print("done")

# TODO: get quarter end dates for current quarter
# print("scraping calendar...")
# page = clientget("https://registrar.ucsc.edu/calendar/future.html")
# soup = BeautifulSoup(page.text, 'lxml', SoupStrainer(['h3', 'td']))
# print(soup)

from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from httpx import Client


print("scraping classroom data...", end="")
client = Client()
classrooms, page = {}, client.get("https://its.ucsc.edu/classrooms/")
soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("select"))
for i in soup.find_all("option")[1:]:
    classrooms[i.text] = f"https://its.ucsc.edu{i['value']}"
catalogDB = deta.Base("catalog")
catalogDB.put(classrooms, "classrooms")
print("done")


print("scraping pisa headers...", end="")
last, store, comp = (
    "",
    [],
    {"action": {"action": ["results", "detail"]}},  # next is adjusted by page
)
page = client.get("https://pisa.ucsc.edu/class_search/index.php")
soup = BeautifulSoup(
    page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
)
# TODO: try to find a way to capture outbound headers of a requested url's post request
# FIXME: GE top level key has weird escape chars
for i in soup:
    if i.name == "label":
        camel = camel_case(i.text.strip())
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
# workaround for https://github.com/deta/deta-python/issues/77
for i in comp:
    for j in comp[i]:
        if isinstance(comp[i][j], dict):
            key = list(comp[i][j].keys())[0]
            if not key:
                value = list(comp[i][j].values())[0]
                del comp[i][j][key]
                comp[i][j] = {"default": value} | comp[i][j]
print("done")
print("building pisa headers...", end="")
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
catalogDB.put(template, "template")
catalogDB.put(outbound, "outbound")
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
