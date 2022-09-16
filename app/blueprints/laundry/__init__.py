from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request

from .helper import *
from app import laundryDB

laundry = Blueprint("laundry", __name__)
laundry_sources = {"LaundryView": "https://www.laundryview.com"}


@laundry.route("/")
def index():
    """Provides residential laundry facility data."""
    return redirect(f"/#{request.blueprint}")


# FIXME: obscenely long response time (~2-3 seconds)
@laundry.route("/rooms")
def rooms():
    """Retrieve data for all residential laundry facilities."""
    return update_rooms(laundryDB.get("rooms"))


@laundry.route("/rooms/<int:id>")
def rooms_id(id: int):
    """Retrieve data for a residential laundry facility. Specify an ID with <code>id</code> (integer). Example: 590391007"""
    rooms = laundryDB.get("rooms")
    if rooms.get(str(id)):
        return update_rooms_id(str(id), rooms)
    abort(404)
