from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request

from .helper import *
from app import catalogDB
from app import condense_args
from app import limiter

catalog = Blueprint("catalog", __name__)
catalog_sources = {
    "RateMyProfessors": "https://www.ratemyprofessors.com/",
    # "UCSC Campus Directory": "https://campusdirectory.ucsc.edu/cd_simple",
    "UCSC Class Search": "https://pisa.ucsc.edu/class_search/",
    "UCSC ITS Classroom Media": "https://its.ucsc.edu/classrooms/",
    # "UCSC TextbookX": "https://ucsc.textbookx.com/institutional/index.php"
}


@catalog.route("/")
def index():
    """Provides academically relative data for campus instructional offerings."""
    return redirect(f"/#{request.blueprint}")


@catalog.route("/rooms")
def rooms():
    """Retrieve all classrooms."""
    rooms = catalogDB.get("rooms")
    del rooms["key"]
    return rooms


@catalog.route("/classrooms")
def classrooms():
    return redirect(f"/#{request.blueprint}")


@catalog.route("/rooms/<string:name>")
def rooms_name(name: str):
    """Retrieve data for a classroom. Specify a name with <code>name</code> (string)."""
    rooms = catalogDB.get("rooms")
    del rooms["key"]
    return get_rooms_name(name, rooms)


@catalog.route("/classrooms/<string:name>")
def classrooms_name(name: str):
    return redirect(f"/#{request.blueprint}")


# TODO: change endpoint name to fit rateMyProfessors
# TODO: https://github.com/Nobelz/RateMyProfessorAPI has a ~2s slower implementation; push a PR
# FIXME: fetch __ref from somewhere
# https://campusdirectory.ucsc.edu/cd_simple
@catalog.route("/rating/<string:name>")
def rating(name: str):
    """Retrieve a RateMyProfessors rating for a teacher. Specify a name with <code>name</code> (string)."""
    return get_rating(name)


@catalog.route("/term", methods=["GET", "POST"])
def term():
    """Retrieve a code for an academic term to use for a class search. Specify a quarter with <code>quarter</code> (string) and/or a year with <code>year</code> (integer)."""
    inbound = condense_args(request, True)
    return get_term(inbound)


# @catalog.route("/classes/calendar", methods=["GET", "POST"])
# def classes_calendar():
#     # TODO: times might override, make a check
#     """Retrieve a generated calendar (<code>.ics</code> file) for specific class(s). Specify class numbers with <code>number</code> (array)."""
#     inbound, client = condense_args(request, True), Client()


# @catalog.route("/courses/calendar", methods=["GET", "POST"])
# def courses_calendar():
#     return redirect(f"/#{request.blueprint}")


@catalog.route("/classes", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes():
    """Retrieve data for a specific class. Specify an optional term with <code>term</code> (integer) and a number with <code>number</code> (integer)."""
    inbound = condense_args(request, True)
    return get_classes(inbound)


@catalog.route("/classes/<int:number>", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes_number(number: int):
    """Retrieve data for a specific class. Specify a number with <code>number</code> (integer)."""
    return get_classes({"number": number})


@catalog.route("/courses", methods=["GET", "POST"])
def courses():
    return redirect(f"/#{request.blueprint}")


# FIXME: ~1.5s response time
# FIXME: verify data type of each k:v pair
# TODO: if only one argument given for a dict, default to most sensible key
# FIXME: page 2 not parsing properly
# FIXME: too high a of a page number returns error
# http://localhost:5000/catalog/classes/search?courseNumber=19
@catalog.route("/classes/search", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes_search():
    """Retrieve class search results. Specify arguments (in their defined data type) accessible at <a href=/catalog/classes/search/template target="_blank" rel="noopener noreferrer">/classes/search/template</a>."""
    inbound = condense_args(request)
    # [curr year relative calendar, increment value]
    template = catalogDB.get("template")
    del template["key"]
    template = template if template else abort(503)
    outbound = catalogDB.get("outbound")
    del outbound["key"]
    return get_classes_search(inbound, template, outbound)


@catalog.route("/courses/search", methods=["GET", "POST"])
def courses_search():
    return redirect(f"/#{request.blueprint}")


@catalog.route("/classes/search/template")
def classes_search_template():
    """Retrieve the template to build your request for <a href=/catalog/classes/search target="_blank" rel="noopener noreferrer">/classes/search</a></code>."""
    template = catalogDB.get("template")
    del template["key"]
    return template if template else abort(503)


@catalog.route("/courses/search/template")
def courses_search_template():
    return redirect(f"/#{request.blueprint}")


@catalog.route("/classes/textbooks")
def classes_textbooks():
    return redirect(f"/#{request.blueprint}")


@catalog.route("/courses/textbooks")
def courses_textbooks():
    return redirect(f"/#{request.blueprint}")


# TODO: use https://ucsc.textbookx.com/institutional/index.php?action=browse#/books/3426324
# @catalog.route("/classes/materials/<id>")
# @catalog.route("/courses/textbooks/<id>")
# def get_textbooks(class_id):
#     """Retrieve materials/textbooks for a specific class number."""
#     pass