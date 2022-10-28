from flask import Blueprint
from flask import redirect
from flask import render_template

from .helper import *

weather = Blueprint("weather", __name__)


@weather.route("/")
def index():
    return render_template("index.html", map=get_index())
