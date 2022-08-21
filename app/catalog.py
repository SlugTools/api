from datetime import datetime
from pprint import pprint
from urllib.parse import quote_plus

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from flask import abort
from flask import Blueprint
from flask import render_template
from flask import request
from orjson import loads
from requests import Session

catalog_bp = Blueprint("catalog", __name__)


@catalog_bp.route("/")
def home():
    return "<h1>Welcome to Catalog!</h1>"


# TODO: https://github.com/Nobelz/RateMyProfessorAPI has a ~2s slower implementation; push a PR
@catalog_bp.route("/teacher/<name>")
async def get_teacher(name):
    # session = Session()
    # sid possibly prone to change
    async with ClientSession() as session:
        page = await session.get(
            f"https://www.ratemyprofessors.com/search/teachers?query={quote_plus(name)}&sid=1078"
        )
        soup = BeautifulSoup(
            await page.text(), "lxml", parse_only=SoupStrainer("script")
        )
        content = {}

        for i in soup:
            if "_ = " in i.text:
                content = loads(i.text[: i.text.index(";")].split("_ = ")[1])
                # using first match at index 4 (relative to sid query parameter)
                # if pushing pr to api library, access reference IDs to make list of teachers
                content = content[list(content.keys())[4]]
                for i in content:
                    if isinstance(content[i], int) and content[i] <= 0:
                        content[i] = None
                break

        # __ref possibly prone to change
        return (
            {
                "name": f"{content['firstName']} {content['lastName']}",
                "department": content["department"],
                "rating": content["avgRating"],
                "ratings": content["numRatings"],
                "difficulty": content["avgDifficulty"],
                "wouldRetake": round(content["wouldTakeAgainPercent"])
                if content["wouldTakeAgainPercent"]
                else None,
                "page": f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={content['legacyId']}",
            }
            if "id" in content and content["school"]["__ref"] == "U2Nob29sLTEwNzg="
            else abort(404)
        )


@catalog_bp.route("/term", methods=["GET", "POST"])  # /term?year=2022&term=spring
def get_term():
    raw = {}
    try:
        raw = request.get_json(force=True)
    except:
        pass
    raw.update(dict(request.args))
    year = int(datetime.now().strftime("%Y"))
    # TODO: fetch from calendar
    quarters, hold = {
        "winter": [datetime(year, 3, 24), 2],
        "spring": [datetime(year, 6, 15), 4],
        "summer": [datetime(year, 9, 1), 6],
        "fall": [datetime(year, 12, 9), 10],
    }, []
    if raw.get("quarter"):
        if not quarters.get(raw.get("quarter").lower()):
            abort(400, "Invalid quarter value.")
        else:
            hold = [raw.get("quarter").lower(), quarters[raw.get("quarter").lower()][1]]
    if raw.get("year"):
        if (
            int(raw.get("year")) <= year
        ):  # FIXME: pisa could list a year ahead, not sure
            year = int(raw.get("year"))
    if not raw.get("quarter"):
        for i in quarters:
            if datetime.today().replace(year=year) < quarters[i][0].replace(year=year):
                hold.append(i)
                hold.append(quarters[i][1])
                break
    # TODO: adjust the function to align with pisa (occ. a quarter ahead)?
    quarter, code = hold[0], 2048 + ((year % 100 - 5) * 10) + hold[1]
    code += 4  # temporary alignment with pisa
    return (
        {"code": code, "term": f"{year} {quarter.capitalize()} Quarter"}
        if code >= 2048
        else abort(400, "Invalid year value.")
    )


# TODO: use https://ucsc.textbookx.com/institutional/index.php?action=browse#/books/3426324
@catalog_bp.route("/class/textbooks/<class_id>")
def get_textbooks(class_id):
    pass


# {
#     "action": [],
#     "term": {},
#     "session": {},
#     "status": {},
#     "subject": {},
#     "courseNumber": {"operation": {}, "value": ""},
#     "courseTitleKeyword": "",
#     "instructorLastName": {"operation": {}, "value": ""},
#     "generalEducation": {},
#     "courseUnits": {"operation": {}, "from": "", "to": "", "exact": ""},
#     "meetingDays": {},
#     "meetingTimes": {},
#     "courseCareer": {},
#     "asynchronousOnline": True,
#     "asynchronousOnline": True,
#     "hybrid": True,
#     "inPerson": True,
#     "page": 1,
# }


@catalog_bp.route("/class/inbound")
def get_pisa():
    with open("app/json/pisa/inbound.json", "r") as f:
        inbound = loads(f.read())
    return inbound if inbound else abort(503)


@catalog_bp.route("/class", methods=["GET", "POST"])
def get_course():
    raw = {}
    try:
        raw = request.get_json(force=True)
    except:
        pass
    raw.update(dict(request.args))
    # [curr year relative calendar, increment value]
    with open("app/json/pisa/inbound.json", "r") as f:
        inbound = loads(f.read())
    if not inbound:
        abort(503)
    with open("app/json/pisa/outbound.json", "r") as f:
        outbound = loads(f.read())

    c = 0
    for i in inbound:
        if isinstance(inbound[i], dict):
            for j in inbound[i]:
                if raw.get(i, {}).get(j):
                    if (
                        isinstance(raw[i][j], (int, str))
                        and str(raw[i][j]).lower() in inbound[i][j]
                    ):
                        outbound[c] = str(raw[i][j])
                c += 1
        elif isinstance(inbound[i], list):
            if raw.get(i):
                if isinstance(raw[i], (int, str)) and str(raw[i]).lower() in inbound[i]:
                    outbound[c] = str(raw[i])
        else:
            if raw.get(i) and isinstance(raw[i], (int, str)):
                outbound[c] = str(raw[i])
        c += 1
    # adjust page
    if raw.get("page") and str(raw["page"]).isnumeric() and raw["page"] > 1:
        outbound["action"] = "next"
        outbound["rec_start"] = str(int(raw.get("page") * 25))
    return outbound
    data = {
        "action": "detail",
        "class_data[:STRM]": "2218",
        "class_data[:CLASS_NBR]": "24373",
    }
    session = Session()
    page = session.post("https://pisa.ucsc.edu/class_search/index.php", data=data)
    soup = BeautifulSoup(page.text, "lxml")
    with open("test.html", "w") as f:
        f.write(soup.prettify())
    return {"success": True}


# @catalog_bp.route("/calendar") # make calendar endpoint
