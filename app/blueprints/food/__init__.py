from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request
from thefuzz.process import extractOne

from .helper import *
from app import condense_args
from app import foodDB

food = Blueprint("food", __name__)
food_sources = {
    "round-nutrition": "https://pypi.org/project/round-nutrition/",
    "UCSC Dining": "https://dining.ucsc.edu/eat/",
    "UCSC Dining Menus": "https://nutrition.sa.ucsc.edu/",
    "UCSC Basic Needs": "https://basicneeds.ucsc.edu/resources/on-campus-food.html",
    "Waitz": "https://waitz.io/ucsc",
}


@food.route("/")
def index():
    """Provides locational and nutritional data for on-campus food/eateries."""
    return redirect(f"/#{request.blueprint}")


# TODO: send without live data
# FIXME: god damn 2.7 second response time
@food.route("/locations")
def locations():
    """Retrieve current locational data for all on-campus dining/eatery locations."""
    locations = foodDB.get("locations")
    del locations["key"]
    return get_locations(locations)


@food.route("/places")
def places():
    return redirect(f"/#{request.blueprint}")


# TODO: update with waitz data upon request
@food.route("/locations/<int:id>")
def locations_id(id: int):
    """Retrieve current locational data for an on-campus dining/eatery location. Specify an ID with <code>id</code> (integer)."""
    locations = foodDB.get("locations")
    del locations["key"]
    location = get_locations_id(locations, id)
    return location if location else abort(404)


@food.route("/places/<int:id>")
def places_id():
    return redirect(f"/#{request.blueprint}")


# TODO: allow enabling date argument
@food.route("/menus", methods=["GET"])
def menus():
    """Retrieve today's menu data for all on-campus and university-managed dining/eatery locations."""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    menus = foodDB.get("menus")
    del menus["key"]
    return menus


@food.route("/menus/<int:id>")
def menus_id(id: int):
    """Retrieve today's menu data for an on-campus and university-managed dining/eatery location. Specify an ID with <code>id</code> (integer)."""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    # TODO: allow enabling date argument
    menus = foodDB.get("menus")
    del menus["key"]
    for i in menus:
        for j in menus[i]:
            if j == str(id):
                return (
                    menus[i][j]
                    if menus[i][j]
                    else abort(204, "The requested menu is empty.")
                )
    abort(404)


@food.route("/items")
def items():
    """Retrieve identifying data for all on-campus university-managed dining/eatery items."""
    items = foodDB.get("items")
    del items["key"]
    return items


@food.route("/items/<string:id>")
def items_id(id: str):
    """Retrieve nutritional data for an on-campus university-managed dining/eatery item. Specify an ID with <code>id</code> (string)."""
    response = scrape_item(id)
    return response if response else abort(404)


# account for item IDs with fractional servings
@food.route("/items/<string:id_1>/<string:id_2>")
def items_id_1_id_2(id_1: str, id_2: str):
    response = scrape_item(f"{id_1}/{id_2}")
    return response if response else abort(404)


@food.route("/items/search/<string:name>")
def items_search_name(name: str):
    """Retrieve item search results. Specify a name with <code>name</code> (string)."""
    items = foodDB.get("items")
    names = list(items.values())
    extract = extractOne(name, names)
    # TODO: adjust threshold
    return (
        {"name": extract[0], "id": list(items.keys())[names.index(extract[0])]}
        if extract[1] > 85
        else abort(404)
    )


# TODO: route for calculating items' total nutritional content
@food.route("/items/sum", methods=["GET", "POST"])
def items_sum():
    """Retrieve summed nutritional data for on-campus university-managed dining/eatery items. Specify IDs with <code>ids</code> (array of strings)."""
    inbound = condense_args(request, True)
    return get_items_sum(inbound)
