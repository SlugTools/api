from flask import Blueprint
from flask import redirect
from flask import render_template
from httpx import get

weather = Blueprint("weather", __name__)


@weather.route("/")
def index():
    req = get("https://wttr.in/Santa+Cruz?format=j1")
    return render_template("index.html", map=get_index())
