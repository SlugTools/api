from flask import Blueprint, redirect, render_template

from .helper import *

home = Blueprint("home", __name__)


@home.route("/")
def index():
    return render_template("index.html", map=get_index())


@home.route("/sources")
def bp_sources():
    from app import sources

    return render_template("sources.html", map=get_sources(), sources=sources)


@home.route("/links")
def links():
    return redirect("/sources")
