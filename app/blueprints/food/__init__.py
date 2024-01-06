from flask import Blueprint, abort, redirect, request
from thefuzz.process import extractOne

from app import condense_args, foodDB

from .helper import *

bp = Blueprint("food", __name__)
srcs = {
    "round-nutrition": "https://pypi.org/project/round-nutrition/",
    "Dining Info": "https://dining.ucsc.edu/eat/",
    "Dining Menus": "https://nutrition.sa.ucsc.edu/",
    # "UCSC Basic Needs": "https://basicneeds.ucsc.edu/resources/on-campus-food.html",
    "Waitz": "https://waitz.io/ucsc",
}


@bp.route("/")
def index():
    """Locations, Menus, and Nutrition"""
    return redirect(f"/#{request.blueprint}")


@bp.route("/locations")
def locations():
    """Details for all locations"""
    locs = foodDB.get("locs")
    return locs["value"]
    # return mult_waitz(locs["value"])


@bp.route("/locations/<int:id>")
def locations_id(id: int):
    """
    Full details for location<br>
    required: <code>id</code> (int)
    Example: 40
    """
    locs = foodDB.get("locs")
    loc = single_waitz(locs["value"], id)
    return loc if loc else abort(404)


# TODO: allow enabling date argument
@bp.route("/menus")
def menus():
    """Basic menu details for all locations"""
    menus = foodDB.get("menus")
    return menus["value"]


# TODO: allow enabling date argument
@bp.route("/menus/<int:id>")
def menus_id(id: int):
    """
    Full menu details for location<br>
    required: <code>id</code> (int)
    Example: 40
    """
    menus = foodDB.get("menus")
    for i in menus["value"]:
        if id == i["id"]:
            return i
    abort(404)


@bp.route("/items")
def items():
    """All food items"""
    items = foodDB.get("items")
    del items["key"]
    return items


@bp.route("/items/<string:id>")
def items_id(id: str):
    """
    Macros for food item<br>
    required: <code>id</code> (int)
    Example: 217008*2*01
    """
    response = scrape_item(id)
    return response if response else abort(404)


# account for item IDs with fractional servings
@bp.route("/items/<string:id_1>/<string:id_2>")
def items_id_frac(id_1: str, id_2: str):
    response = scrape_item(f"{id_1}/{id_2}")
    return response if response else abort(404)


@bp.route("/items/search/<string:name>")
def items_search_name(name: str):
    """
    Search for food item by name<br>
    required: <code>name</code> (str)
    Example: Corn
    """
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
    """
    Summed macros for items<br>
    required: <code>ids</code> (arr of str)
    """
    inbound = condense_args(request, True)
    return get_items_sum(inbound)
