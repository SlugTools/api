# from deta import Deta
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config

# from .scraper.locations import scrape_locations
# from .scraper.menus import scrape_menus

print("instantiating app...")
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

from app import catalog, errors, food, home, laundry

app.register_blueprint(home.home_bp)
app.register_blueprint(food.food_bp, url_prefix="/food")
app.register_blueprint(laundry.laundry_bp, url_prefix="/laundry")

# # TODO: get quarter end dates for current quarter
# page = get('https://registrar.ucsc.edu/calendar/future.html')
# soup = BeautifulSoup(page.text, 'lxml', SoupStrainer(['h3', 'td']))
# print(soup)

# # TODO: get subject codes, etc.
# page = get('https://pisa.ucsc.edu/class_search/index.php')
# soup = BeautifulSoup(page.text, 'lxml')

app.register_blueprint(catalog.catalog_bp, url_prefix="/catalog")
# TODO: maybe a calender blueprint?
