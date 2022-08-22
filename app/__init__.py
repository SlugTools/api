# from deta import Deta
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sentry_sdk import init
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config

print("instantiating app and extensions...", end="")
app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)
print("done")

print("initiating sentry...", end="")
init(
    dsn=app.config["SENTRY_SDK_DSN"],
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
)
print("done")

# from .scraper.locations import scrape_locations
# from .scraper.menus import scrape_menus

# print("scraping for food blueprint...", end="")
# deta = Deta(app.config["DETA_KEY"])
# locationsDB = deta.Base("locations")
# locationsDB.put(scrape_locations())
# menusDB = deta.Base("menus")
# menusDB.put(scrape_menus(datetime.now().strftime('%m-%d-%Y')))
# print("done")

# TODO: get quarter end dates for current quarter
# print("scraping calendar...")
# page = get('https://registrar.ucsc.edu/calendar/future.html')
# soup = BeautifulSoup(page.text, 'lxml', SoupStrainer(['h3', 'td']))
# print(soup)

print("scraping pisa outbound headers...", end="")
from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from requests import Session
from orjson import dumps
from re import sub

session, last, store, comp = (
    Session(),
    "",
    [],
    {"action": {"action": ["results", "detail"]}},  # next is adjusted by page
)
page = session.get("https://pisa.ucsc.edu/class_search/index.php")
soup = BeautifulSoup(
    page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
)
with open("testing/main.html", "w") as f:
    f.write(soup.prettify())
for i in soup:
    if i.name == "label":
        snake = sub(r"(_|-)+", " ", i.text.strip()).title().replace(" ", "")
        camel = snake[0].lower() + snake[1:]
        if i.get("class") == ["col-sm-2", "form-control-label"]:
            comp[camel], last = {}, camel
        # FIXME: courseTitleKeywords left blank
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
# most sane approach to counter empty courseTitleKeywords
last = ""
for i in comp:
    if len(comp[i]) == 0:
        transfer = [list(comp[last].keys())[-1], list(comp[last].values())[-1]]
        del comp[last][transfer[0]]
        comp[i][transfer[0]] = transfer[1]
    last = i
print("building pisa inbound headers...", end="")
inbound = {}
for i in comp:
    if len(comp[i]) != 1:
        inbound[i] = {}
        for j in comp[i]:
            if j[:-1].split("_")[-1] == "op":
                inbound[i]["operation"] = comp[i][j]
            elif j[:-1].split("_")[-1] == "nbr" or "_" not in j:
                inbound[i]["value"] = comp[i][j]
            else:
                inbound[i][j[:-1].split("_")[-1]] = comp[i][j]
    else:
        inbound[i] = comp[i][list(comp[i].keys())[0]]
outbound = {}
for i in comp:
    for j in comp[i]:
        if isinstance(comp[i][j], dict):
            outbound[j] = list(comp[i][j].keys())[0]
        elif isinstance(comp[i][j], list):
            outbound[j] = comp[i][j][0]
        else:
            outbound[j] = comp[i][j]
inbound["page"], outbound["rec_start"], outbound["rec_dur"] = 1, "0", "25"
if len(inbound) == 2:
    inbound, outbound = None, None
with open("app/data/json/pisa/inbound.json", "wb") as f:
    f.write(dumps(inbound))
with open("app/data/json/pisa/outbound.json", "wb") as f:
    f.write(dumps(outbound))
print("done")

print("instantiating blueprints...", end="")
from app import catalog, errors, food, home, laundry

app.register_blueprint(home.home_bp)
# disclaimers for nutrition: "email bvanotte@ucsc.edu"
app.register_blueprint(food.food_bp, url_prefix="/food")
app.register_blueprint(laundry.laundry_bp, url_prefix="/laundry")
app.register_blueprint(catalog.catalog_bp, url_prefix="/catalog")
# metro endpoint: https://www.scmtd.com/en/routes/schedule
# app.register_blueprint(catalog.catalog_bp, url_prefix="/metro")
# TODO: maybe an instructional calender blueprint?
print("done")
