from flask import Blueprint, redirect, render_template
from httpx import get

bp = Blueprint("weather", __name__)
srcs = {"nothing": "yet"}


@bp.route("/")
def index():
    # req = get("https://wttr.in/Santa+Cruz?format=j1")
    return "in progress"
