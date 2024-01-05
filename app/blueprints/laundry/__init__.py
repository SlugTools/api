from flask import Blueprint, abort, redirect, request

from app import laundryDB

from .helper import *

bp = Blueprint("laundry", __name__)
srcs = {"LaundryView": "https://www.laundryview.com"}


@bp.route("/")
def index():
    """Laundry Rooms"""
    return redirect(f"/#{request.blueprint}")


# FIXME: obscenely long response time (~2-3 seconds)
@bp.route("/rooms")
def rooms():
    """Details for all laundry rooms"""
    return update_rooms(laundryDB.get("rooms"))


@bp.route("/rooms/<int:id>")
def rooms_id(id: int):
    """
    Details for laundry room<br>
    required: <code>id</code> (int)
    Example: 590391007
    """
    rooms = laundryDB.get("rooms")
    if rooms.get(str(id)):
        return update_rooms_id(str(id), rooms)
    abort(404)
