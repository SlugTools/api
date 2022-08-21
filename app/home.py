from __future__ import division

import os

from flask import Blueprint
from flask import render_template
from flask import send_from_directory

from app import app

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():
    return render_template("home.html")


# FIXME: this 404's
@home_bp.route("/favicon.ico")
def get_favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")


@home_bp.route("/debug-sentry")
def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero
