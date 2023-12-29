from flask import Blueprint, abort, redirect, request
from thefuzz.process import extractOne

from app import condense_args, foodDB

from .helper import *

bp = Blueprint("food", __name__)
srcs = {
    "round-nutrition": "https://pypi.org/project/round-nutrition/",
    "UCSC Dining": "https://dining.ucsc.edu/eat/",
    "UCSC Dining Menus": "https://nutrition.sa.ucsc.edu/",
    "UCSC Basic Needs": "https://basicneeds.ucsc.edu/resources/on-campus-food.html",
    "Waitz": "https://waitz.io/ucsc",
}


@bp.route("/")
def index():
    """Provides locational and nutritional data for on-campus food/eateries."""
    return redirect(f"/#{request.blueprint}")


@bp.route("/locations")
def locations():
    """Retrieve current locational data for all on-campus dining/eatery locations."""
    locations = foodDB.get("locations")
    del locations["key"]
    return locations
    return update_locations(locations)


@bp.route("/places")
def places():
    return redirect(f"/#{request.blueprint}")


@bp.route("/locations/<int:id>")
def locations_id(id: int):
    """Retrieve current locational data for an on-campus dining/eatery location. Specify an ID with <code>id</code> (integer). Example: 40"""
    location = update_locations_id(foodDB.get("locations"), id)
    return location if location else abort(404)


@bp.route("/places/<int:id>")
def places_id():
    return redirect(f"/#{request.blueprint}")


# TODO: allow enabling date argument
@bp.route("/menus", methods=["GET"])
def menus():
    """Retrieve today's menu data for all on-campus and university-managed dining/eatery locations."""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    menus = foodDB.get("menus")
    del menus["key"]
    return menus


# TODO: allow enabling date argument
@bp.route("/menus/<int:id>")
def menus_id(id: int):
    """Retrieve today's menu data for an on-campus and university-managed dining/eatery location. Specify an ID with <code>id</code> (integer). Example: 40"""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    menus = foodDB.get("menus")
    for i in menus:
        for j in menus[i]:
            if j == str(id):
                return (
                    menus[i][j]
                    if menus[i][j]
                    else abort(204, "The requested menu is empty.")
                )
    abort(404)


@bp.route("/items")
def items():
    """Retrieve identifying data for all on-campus university-managed dining/eatery items."""
    items = foodDB.get("items")
    del items["key"]
    return items


@bp.route("/items/<string:id>")
def items_id(id: str):
    """Retrieve nutritional data for an on-campus university-managed dining/eatery item. Specify an ID with <code>id</code> (string). Example: 217008*2*01"""
    response = scrape_item(id)
    return response if response else abort(404)


# account for item IDs with fractional servings
@bp.route("/items/<string:id_1>/<string:id_2>")
def items_id_1_id_2(id_1: str, id_2: str):
    response = scrape_item(f"{id_1}/{id_2}")
    return response if response else abort(404)


@bp.route("/items/search/<string:name>")
def items_search_name(name: str):
    """Retrieve item search results. Specify a name with <code>name</code> (string). Example: Corn"""
    items = foodDB.get("items")
    names = list(items.values())
    extract = extractOne(name, names)
    return (
        {"name": extract[0], "id": list(items.keys())[names.index(extract[0])]}
        if extract[1] > 85
        else abort(404)
    )


@bp.route("/items/sum", methods=["GET", "POST"])
def items_sum():
    """Retrieve summed nutritional data for on-campus university-managed dining/eatery items. Specify IDs with <code>ids</code> (array of strings)."""
    inbound = condense_args(request, True)
    return get_items_sum(inbound)
