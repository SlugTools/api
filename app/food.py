from datetime import datetime

from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request

from .scraper.items import scrape_item
from .scraper.locations import get_location
from .scraper.locations import scrape_locations
from .scraper.menus import get_menu
from .scraper.menus import scrape_menus
from app import condense_received

# FIXME: types for all parameters, route functions, and call functions
# TODO: find way to preload base site cookies without including get statement in each function

food = Blueprint("food", __name__)


@food.route("/")
def index():
    """Provides locational and nutritional data for on-campus food/eateries."""
    return redirect("/#food")


# TODO: update with waitz data upon request
@food.route("/locations")
def import_locations():
    """Get all on-campus food/eateries location data."""
    return scrape_locations()
    # response = locationsDB.fetch().items[0]
    # del response['key']
    # pprint(response)
    # return response if response else abort(500)


# @food.route("/locations/<int:id>")
# def import_location(id: int):
#     response = get_location(id)
#     return response if response else abort(404)
#     locations = locationsDB.fetch().items[0]
#     del locations["key"]
#     response = None
#     for i in locations:
#         for j in locations[i]:
#             if j["id"] == location_id:
#                 return response
#     abort(404)


@food.route("/menus", methods=["GET", "POST"])
def import_menus():
    """Get today's menu data for all on-campus dining/eatery locations. Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    inbound = condense_received(request)
    date = datetime.now().strftime("%m-%d-%Y")
    if inbound.get("date"):
        date = inbound.get("date")
    response = scrape_menus(date)
    return response if response else abort(404)


@food.route("/menus/<int:id>")
def import_menu(id: int):
    """Get today's menu data for an on-campus dining/eatery location. Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    inbound = condense_received(request)
    date = datetime.now().strftime("%m-%d-%Y")
    if inbound.get("date"):
        date = inbound.get("date")
    response = get_menu(id, date)
    return response if response else abort(404)


@food.route("/items")
def forward_item():
    return redirect("/#food-items")


@food.route("/items/<id>")
def import_item(id):
    """Get nutritional data for a on-campus university-managed dining/eatery location."""
    response = scrape_item(id)
    return response if response else abort(204)


# account for item IDs with fractional servings
@food.route("/items/<id_1>/<id_2>")
def import_frac_item(id_1, id_2):
    response = scrape_item(f"{id_1}/{id_2}")
    return response if response else abort(404)
