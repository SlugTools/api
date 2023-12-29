from flask import Blueprint, redirect, render_template

from .helper import *

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    return render_template("index.html", map=get_index())


@bp.route("/sources")
def bp_sources():
    from app import sources

    return render_template("sources.html", map=get_sources(), sources=sources)


@bp.route("/links")
def links():
    return redirect("/sources")
