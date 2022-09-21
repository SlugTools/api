from re import findall
from re import sub
from threading import Event
from threading import Thread
from time import sleep
from unicodedata import normalize

from apscheduler.schedulers.background import BackgroundScheduler
from deta import Deta
from flask import Flask
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from httpx import Client
from schedule import every
from schedule import run_pending
from sentry_sdk import init
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

from config import Config


# TODO: add option to disable data scraping
def create_app() -> Flask:
    print("initializing app...", end="", flush=True)
    app = Flask(__name__)
    app.config.from_object(Config)
    print("done")
    return app


app = create_app()


print("defining helper functions...", end="", flush=True)


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
    inbound.update(dict(request.args))  # could use "**" operators
    return {k.lower(): v for k, v in inbound.items()} if lower else inbound


def force_to_int(text):
    if any([c.isdigit() for c in text]):
        return int(sub(r"\D", "", text))
    return text


# TODO: currently works as a temp fix; rework to reach all sublevels
# construct lexicographically sorted data by adding preceding two-digit index
def forge(data):
    keys = list(data.keys())
    return {f"{(i + 1):02d}{keys[i]}": v[1] for i, v in enumerate(data.items())}


# TODO: currently works as a temp fix; rework to reach all sublevels
# deconstruct lexicographically sorted data by removing preceding two-digit index
def melt(data):
    return {k[2:]: v for k, v in data.items() if k != "key"}


def parse_days_times(text):
    text = text.split(" ")
    days = {
        "M": "Monday",
        "Tu": "Tuesday",
        "W": "Wednesday",
        "Th": "Thursday",
        "F": "Friday",
        "Sa": "Saturday",
        "Su": "Sunday",
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


def scrape_data(client=None):
    def scrape_catalog(client):
        # TODO: get quarter end dates for current quarter
        # print("scraping calendar...")
        # page = client.get("https://registrar.ucsc.edu/calendar/future.html")
        # soup = BeautifulSoup(page.text, "lxml", SoupStrainer(["h3", "td"]))
        # print(soup)
        from .start.catalog import scrape_rooms, build_headers

        print("scraping room data...", end="", flush=True)
        rooms = scrape_rooms(client)
        print("done\nbuilding pisa headers...")
        pisa = build_headers(client)
        print("done")
        return {"rooms": rooms, "template": pisa[0], "outbound": pisa[1]}

    def scrape_food(client):
        from .start.food import scrape_locations, scrape_menus_items

        print("scraping locational data...", end="", flush=True)
        locations = scrape_locations(client)
        print("done\nscraping menu data...", end="", flush=True)
        menus_items = scrape_menus_items(client, locations)
        print("done")
        return {
            "locations": locations,
            "menus": menus_items[0],
            "items": menus_items[1],
        }

    def scrape_laundry(client):
        from .start.laundry import scrape_laundry_rooms

        print("scraping laundry data...", end="", flush=True)
        rooms = scrape_laundry_rooms(client)
        print("done")
        return {"rooms": rooms}

    catalog = scrape_catalog(client)
    food = scrape_food(client)
    laundry = scrape_laundry(client)
    print("saving to databases...", end="", flush=True)
    catalogDB.put(catalog["rooms"], "rooms")
    catalogDB.put(forge(catalog["template"]), "template")
    catalogDB.put(forge(catalog["outbound"]), "outbound")
    foodDB.put(food["locations"], "locations")
    foodDB.put(food["menus"], "menus")
    foodDB.put(food["items"], "items")
    laundryDB.put(laundry["rooms"], "rooms")
    print("done")


def register_blueprints(app):
    from . import errors
    from .blueprints.home import home
    from .blueprints.catalog import catalog, catalog_sources
    from .blueprints.food import food, food_sources
    from .blueprints.laundry import laundry, laundry_sources

    print("fetching sources...", end="", flush=True)
    # TODO: better way of fetching sources
    sources = {
        "/catalog": catalog_sources,
        "/food": food_sources,
        "/laundry": laundry_sources,
    }
    print("done")
    # TODO: implement nested blueprints?
    print("registering blueprints...", end="", flush=True)
    app.register_blueprint(home)
    app.register_blueprint(catalog, url_prefix="/catalog")
    app.register_blueprint(food, url_prefix="/food")
    app.register_blueprint(laundry, url_prefix="/laundry")
    # TODO: metro endpoint; https://www.scmtd.com/sen/routes/schedule
    # app.register_blueprint(metro, url_prefix="/metro")
    # TODO: weather endpoint
    # app.register_blueprint(weather, url_prefix="/weather")
    # TODO: maybe an instructional calender blueprint?
    print("done")
    return sources


with app.app_context():
    print("initializing extensions...", end="", flush=True)
    Compress(app)
    CORS(app)
    deta = Deta(app.config["DETA_KEY"])
    # TODO: set up limits
    limiter = Limiter(app, key_func=get_remote_address)
    # init(
    #     dsn=app.config["SENTRY_SDK_DSN"],
    #     integrations=[FlaskIntegration(), HttpxIntegration()],
    #     traces_sample_rate=1.0,
    # )
    print("done")
    print("declaring databases...", end="", flush=True)
    catalogDB = deta.Base("catalog")
    foodDB = deta.Base("food")
    laundryDB = deta.Base("laundry")
    print("done")
    client = Client()
    # scrape_data(Client())
    sources = register_blueprints(app)
    # print("registering event loops...", end="", flush=True)
    # def run_continuously(interval=1):
    #     cease_continuous_run = Event()

    #     class ScheduleThread(Thread):
    #         @classmethod
    #         def run(cls):
    #             while not cease_continuous_run.is_set():
    #                 run_pending()
    #                 sleep(interval)

    #     continuous_thread = ScheduleThread()
    #     continuous_thread.start()
    #     return cease_continuous_run

    # every().minute.do(scrape_data, client=Client())
    # stop_run_continuously = run_continuously()
    # print("done")
