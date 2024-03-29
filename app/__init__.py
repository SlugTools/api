# from threading import Event
# from time import sleep

import sys
import warnings

from deta import Deta
from flask import Flask
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from httpx import Client

# from schedule import every
from sentry_sdk import init
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

from config import Config


# TODO: add option to disable data scraping
def create_app() -> Flask:
    print("\ninitializing app...", end="", flush=True)
    app = Flask(__name__)
    app.config.from_object(Config)
    print("done")
    return app


app = create_app()

print("defining helper functions...", end="", flush=True)
from .helper import *

print("done")
from .start import catalog, food, laundry


def scrape_data(cli):
    def scrape_catalog(cli):
        print("scraping room data...", end="", flush=True)
        rooms = catalog.scrape_rooms(cli)
        print("done\nscraping pisa headers...", end="", flush=True)
        inB, outB = catalog.build_headers(cli)
        print("done")
        return [rooms, inB, outB]

    def scrape_food(cli):
        print("scraping location data...", end="", flush=True)
        locs = food.scrape_locations(cli)
        locs = list(locs.values())
        print("done\nscraping menu data...", end="", flush=True)
        menus, items = food.scrape_menus_items(locs)
        print("done")
        return [locs, menus, items]

    def scrape_laundry(cli):
        print("scraping laundry data...", end="", flush=True)
        rooms = laundry.scrape_rooms(cli)
        print("done")
        return rooms

    cat = scrape_catalog(cli)
    fd = scrape_food(cli)
    ld = scrape_laundry(cli)
    print("saving to databases...", end="", flush=True)
    catalogDB.put(cat[0], "rooms")
    catalogDB.put(forge(cat[1]), "inB")  # template for users on how to build headers
    catalogDB.put(forge(cat[2]), "outB")  # pisa site-readable headers
    foodDB.put(fd[0], "locs")
    foodDB.put(fd[1], "menus")
    foodDB.put(fd[2], "items")
    laundryDB.put(ld, "rooms")
    print("done")


def register_blueprints(app):
    from . import errors
    from .blueprints import catalog, food, home, laundry, weather

    print("registering blueprints...", end="", flush=True)
    app.register_blueprint(home.bp)
    app.register_blueprint(catalog.bp, url_prefix="/catalog")
    app.register_blueprint(food.bp, url_prefix="/food")
    app.register_blueprint(laundry.bp, url_prefix="/laundry")
    # app.register_blueprint(metro.bp, url_prefix="/metro")
    app.register_blueprint(weather.bp, url_prefix="/weather")
    print("done\n")

    return {
        "/catalog": catalog.srcs,
        "/food": food.srcs,
        "/laundry": laundry.srcs,
        # "/metro": metro.srcs,
        "/weather": weather.srcs,
    }


with app.app_context():
    print("initializing extensions...", end="", flush=True)
    Compress(app)
    CORS(app)
    deta = Deta(app.config["DETA_KEY"])
    warnings.filterwarnings("ignore")
    limiter = Limiter(get_remote_address, app=app)  # TODO: review limits
    if "--debug" not in sys.argv:
        init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration(), HttpxIntegration()],
            traces_sample_rate=1.0,
        )

    print("done\ndeclaring databases...", end="", flush=True)
    catalogDB = deta.Base("catalog")
    foodDB = deta.Base("food")
    laundryDB = deta.Base("laundry")
    print("done")

    currTerm = list(catalogDB.get("template")["02term"].values())[-1]

    if "--noscrape" not in sys.argv:
        scrape_data(Client(verify=False))

    srcs = register_blueprints(app)
    # print("registering event loops...", end="", flush=True)
    # every().day.at("00:00").do(scrape_data, client=Client())
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

# general app TODOs
# TODO: metro info - https://www.scmtd.com/sen/routes/schedule
# TODO: weather info - local
# TODO: library room booking wait times
# TODO: instructional calender info
# TODO: cbord get app integration
# TODO: synchronize aborts (203's, etc.) across all blueprints
# TODO: set up custom errors for abort() calls
# TODO: configure sentry and newrelic
# TODO: use markupsafe to parse arguments/headers
# TODO: fix all deep source errors
# TODO: push pr for thunder folder
# TODO: advertise through fresh paint etc.
# TODO: google seo
# TODO: cut out all post requests, cuz no modification on local end
# TODO: use Soup Strainer for all?
# TODO: set up flask monitoring dashboard
# TODO: migrate to quart (use async data, sentry-sdk[quart])

# implement
# flask-mail # emailer
# laundry view # laundry viewer
# # implement later
# flask-wtf # form validation
# celery database # queue workers
# flask-migrate # database migrations
# flask-sqlalchemy # database
# gunicorn # web server
# hiredis # C client for Redis
# psycopg2 # DB API for PostgreSQL
# redis # queue for database
# pyjwt # JSON web tokens
# flask-cas # CAS authentication with CBORD
