# from deta import Deta
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config

# from .scraper.locations import scrape_locations
# from .scraper.menus import scrape_menus

print("instantiating app and extensions...", end="")
app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)
# deta = Deta(app.config["DETA_KEY"])
# locationsDB = deta.Base("locations")
# locationsDB.put(scrape_locations())
# menusDB = deta.Base("menus")
# menusDB.put(scrape_menus(datetime.now().strftime('%m-%d-%Y')))
print("done")


# TODO: get quarter end dates for current quarter
# print("scraping calendar...")
# page = get('https://registrar.ucsc.edu/calendar/future.html')
# soup = BeautifulSoup(page.text, 'lxml', SoupStrainer(['h3', 'td']))
# print(soup)

# preload catalog class selectable options
print("scraping catalog class website...", end="")
from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from requests import Session
from orjson import dumps

session, opt = Session(), {}
page = session.get("https://pisa.ucsc.edu/class_search/index.php")
# FIXME: fix lxml parsing
soup = BeautifulSoup(page.text, "html.parser", parse_only=SoupStrainer("select"))
for i in soup:
    opt[i["name"]] = {}
    for j in i:
        if isinstance(j, NavigableString):
            continue
        opt[i["name"]][j["value"]] = j.text
obj = dumps(opt)
# display these options to catalog site
with open("app/class_codes.json", "wb") as f:
    f.write(obj)
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
