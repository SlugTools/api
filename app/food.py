from datetime import datetime
from pprint import pprint

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import request

from .scraper.items import scrape_item
from .scraper.locations import get_location
from .scraper.locations import scrape_locations
from .scraper.menus import get_menu
from .scraper.menus import scrape_menus

# import flask_monitoringdashboard as dashboard
# dashboard.config.init_from(file='config.cfg')

# FIXME: types for all parameters, route functions, and call functions
# TODO: find way to preload base site cookies without including get statement in each function

food_bp = Blueprint("food", __name__)


@food_bp.route("/")
def home():
    return "<h1>Welcome to Food!</h1>"


@food_bp.route("/locations")
def import_locations():
    return scrape_locations()
    # response = locationsDB.fetch().items[0]
    # del response['key']
    # pprint(response)
    # return response if response else abort(500)


# @food_bp.route("/locations/<int:location_id>")
# def import_location(location_id: int):
#     response = get_location(location_id)
#     return response if response else abort(404)
#     locations = locationsDB.fetch().items[0]
#     del locations["key"]
#     response = None
#     for i in locations:
#         for j in locations[i]:
#             if j["id"] == location_id:
#                 return response
#     abort(404)


@food_bp.route("/menus")
def import_menus():
    date = datetime.now().strftime("%m-%d-%Y")
    if request.args.get("date"):
        date = request.args.get("date")
    response = scrape_menus(date)
    return response if response else abort(404)


@food_bp.route("/menus/<int:location_id>")
def import_menu(location_id: int):
    date = datetime.now().strftime("%m-%d-%Y")
    if request.args.get("date"):
        date = request.args.get("date")
    response = get_menu(location_id, date)
    return response if response else abort(404)


@food_bp.route("/items/<item_id>")
def import_item(item_id):
    response = scrape_item(item_id)
    return response if response else abort(404)


# account for item IDs with fractional servings
@food_bp.route("/items/<item_id1>/<item_id2>")
def import_frac_item(item_id1, item_id2):
    response = scrape_item(f"{item_id1}/{item_id2}")
    return response if response else abort(404)
