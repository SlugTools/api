from re import search

from flask import Blueprint, abort, redirect, request

from app import catalogDB, condense_args, limiter, melt

from .helper import *

bp = Blueprint("catalog", __name__)
srcs = {
    "RateMyProfessors": "https://www.ratemyprofessors.com/",
    # "UCSC Campus Directory": "https://campusdirectory.ucsc.edu/cd_simple",
    "UCSC Class Search": "https://pisa.ucsc.edu/class_search/",
    "UCSC ITS Classroom Media": "https://its.ucsc.edu/classrooms/",
    # "UCSC TextbookX": "https://ucsc.textbookx.com/institutional/index.php"
}


@bp.route("/")
def index():
    """Provides academically relative data for campus instructional offerings."""
    return redirect(f"/#{request.blueprint}")


@bp.route("/rooms")
def rooms():
    """Retrieve all classrooms."""
    rooms = catalogDB.get("rooms")
    del rooms["key"]
    return rooms


@bp.route("/classrooms")
def classrooms():
    return redirect(f"/#{request.blueprint}")


@bp.route("/rooms/<string:name>")
def rooms_name(name: str):
    """Retrieve data for a classroom. Specify a name with <code>name</code> (string). Example: Classroom Unit 001"""
    return get_rooms_name(name, catalogDB.get("rooms"))


@bp.route("/classrooms/<string:name>")
def classrooms_name(name: str):
    return redirect(f"/#{request.blueprint}")


# TODO: https://github.com/Nobelz/RateMyProfessorAPI has a ~2s slower implementation; push a PR
# FIXME: fetch __ref from somewhere
@bp.route("/ratings/<string:name>")
def ratings(name: str):
    """Retrieve a RateMyProfessors rating for a teacher. Specify a name with <code>name</code> (string). Example: Luca De Alfaro"""
    return get_ratings(name)


@bp.route("/term", methods=["GET", "POST"])
def term():
    """Retrieve a code for an academic term to use for a class search. Specify a quarter with <code>quarter</code> (string) and/or a year with <code>year</code> (integer)."""
    inbound = condense_args(request, True)
    return get_term(inbound)


# @bp.route("/classes/calendar", methods=["GET", "POST"])
# def classes_calendar():
#     # TODO: times might override, make a check
#     """Retrieve a generated calendar (<code>.ics</code> file) for specific class(s). Specify class numbers with <code>number</code> (array)."""
#     inbound, client = condense_args(request, True), Client()


# @bp.route("/courses/calendar", methods=["GET", "POST"])
# def courses_calendar():
#     return redirect(f"/#{request.blueprint}")


@bp.route("/classes", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes():
    """Retrieve data for a specific class. Specify an optional term with <code>term</code> (integer) and a number with <code>number</code> (integer)."""
    inbound = condense_args(request, True)
    return get_classes(inbound)


@bp.route("/classes/<int:number>", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes_number(number: int):
    """Retrieve data for a specific class for the current term. Specify a number with <code>number</code> (integer). Example: 10495"""
    return get_classes({"number": number})


@bp.route("/courses", methods=["GET", "POST"])
def courses():
    return redirect(f"/#{request.blueprint}")


# FIXME: ~1.5s response time
# FIXME: too high a of a page number returns error
# http://localhost:5000/catalog/classes/search?courseNumber=19
@bp.route("/classes/search", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes_search():
    """Retrieve class search results. Specify argument(s) (in their defined data type) accessible at <a href=/catalog/classes/search/template target="_blank" rel="noopener noreferrer">/classes/search/template</a>."""
    inbound = condense_args(request)
    # [curr year relative calendar, increment value]
    template = melt(catalogDB.get("template"))
    template = template if template else abort(503)
    outbound = melt(catalogDB.get("outbound"))
    return get_classes_search(inbound, template, outbound)


@bp.route("/classes/search/<string:code>", methods=["GET", "POST"])
@limiter.limit("5/minute")
def classes_search_name(code: str):
    """Retrieve class search results. Specify a subject and a number following it with <code>code</code> (string). Example: MATH 19A"""
    # [curr year relative calendar, increment value]
    template = melt(catalogDB.get("template"))
    template = template if template else abort(503)
    outbound = melt(catalogDB.get("outbound"))
    match = search(r"\d", code)
    match = (
        match.start()
        if match
        else abort(
            400,
            "The argument <code>code</code> should have a subject and a number following it.",
        )
    )
    return get_classes_search(
        {"subject": code[:match], "courseNumber": code[match:]}, template, outbound
    )


@bp.route("/courses/search", methods=["GET", "POST"])
def courses_search():
    return redirect(f"/#{request.blueprint}")


@bp.route("/classes/search/template")
def classes_search_template():
    """Retrieve the template to build your request for <a href=/catalog/classes/search target="_blank" rel="noopener noreferrer">/classes/search</a></code>."""
    template = melt(catalogDB.get("template"))
    for i in template:
        if isinstance(template[i], dict) and template[i].get("default-"):
            template[i][""] = template[i].pop("default-")
    return template if template else abort(503)


@bp.route("/courses/search/template")
def courses_search_template():
    return redirect(f"/#{request.blueprint}")


@bp.route("/classes/textbooks")
def classes_textbooks():
    return redirect(f"/#{request.blueprint}")


@bp.route("/courses/textbooks")
def courses_textbooks():
    return redirect(f"/#{request.blueprint}")


# https://ucsc.textbookx.com/institutional/index.php?action=browse#/books/3426324
# @catalog.route("/classes/materials/<id>")
# @catalog.route("/courses/textbooks/<id>")
# def get_textbooks(class_id):
#     """Retrieve materials/textbooks for a specific class number."""
#     pass
