from datetime import datetime
from pprint import pprint

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import request

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():
    return render_template("home.html")
