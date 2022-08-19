# from deta import Deta
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config


print("instantiating app and extensions...", end="")
app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)
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

print("scraping for catalog blueprint...", end="")
from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from requests import Session
from orjson import dumps
from re import sub

session, cat = Session(), {}
page = session.get("https://pisa.ucsc.edu/class_search/index.php")
soup = BeautifulSoup(
    page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
)
last, store, cat = "", [], {"action": {"action": ["results", "detail"]}}
for i in soup:
    if i.name == "label":
        snake = sub(r"(_|-)+", " ", i.text.strip()).title().replace(" ", "")
        camel = snake[0].lower() + snake[1:]
        if i.get("class") == ["col-sm-2", "form-control-label"]:
            cat[camel], last = {}, camel
        # FIXME: #3 courseTitleKeywords left blank
        elif i.get("class") == ["sr-only"]:
            cat[last]["input"] = ""
        elif i.find("input"):
            cat[camel] = {i.find("input")["name"]: True}
    elif i.name == "select":
        options = {}
        for j in i:
            if isinstance(j, NavigableString):
                continue
            options[j["value"]] = j.text
        cat[last][i["name"]] = options
        if "input" in cat[last]:
            del cat[last]["input"]
            store.append(last)
    elif i.name == "input":
        if i.get("type") == "text":
            cat[store[-1]][i["name"]] = ""

# counter ['sr-only'] issue
last = ""
for i in cat:
    if len(cat[i]) == 0:
        transfer = [list(cat[last].keys())[-1], list(cat[last].values())[-1]]
        del cat[last][transfer[0]]
        cat[i][transfer[0]] = transfer[1]
    last = i

cat["page"] = {"rec_start": 0, "rec_dur": 25}

with open("app/json/pisa.json", "wb") as f:
    f.write(dumps(cat))
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
