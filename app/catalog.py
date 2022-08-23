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
from thefuzz import process

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


@catalog_bp.route("/term", methods=["GET", "POST"])
def get_term():
    inbound = {}
    try:
        inbound = request.get_json(force=True)
    except:
        pass
    inbound.update(dict(request.args))
    year = int(datetime.now().strftime("%Y"))
    # TODO: fetch from calendar
    quarters, hold = {
        "winter": [datetime(year, 3, 24), 2],
        "spring": [datetime(year, 6, 15), 4],
        "summer": [datetime(year, 9, 1), 6],
        "fall": [datetime(year, 12, 9), 10],
    }, []
    if inbound.get("quarter"):
        if not quarters.get(inbound.get("quarter").lower()):
            abort(400, "Invalid quarter value.")
        else:
            hold = [
                inbound.get("quarter").lower(),
                quarters[inbound.get("quarter").lower()][1],
            ]
    if inbound.get("year"):
        if (
            int(inbound.get("year")) <= year
        ):  # FIXME: pisa could list a year ahead, not sure
            year = int(inbound.get("year"))
    if not inbound.get("quarter"):
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


@catalog_bp.route("/class/template")
def get_pisa():
    with open("app/data/json/pisa/template.json", "r") as f:
        template = loads(f.read())
    return template if template else abort(503)


@catalog_bp.route("/class", methods=["GET", "POST"])
def get_course():
    inbound = {}
    try:
        inbound = request.get_json(force=True)
    except:
        pass
    inbound.update(dict(request.args))
    # [curr year relative calendar, increment value]
    with open("app/data/json/pisa/template.json", "r") as f:
        template = loads(f.read())
    # TODO: enable case insensitivity for inbound headers
    # modified = template.copy()
    # for i in modified:
    #     if isinstance(modified[i], dict):
    #         for j in modified:
    #             if isinstance(modified[j], dict):
    #                 if modified[j].get("name") == inbound.get(i):
    #                     modified[i] = modified[j]
    #                     break
    # template = [i.lower() for i in template for j in] if template else abort(503)
    with open("app/data/json/pisa/outbound.json", "r") as f:
        outbound = loads(f.read())
    c, extract = 0, ()
    keys = list(outbound.keys())
    # TODO: abort with 500 for invalid types, or use default?
    # TODO: adjust ratio threshold for fuzzy matching
    # FIXME: operation keys not getting fuzzy matches properly
    # TODO: integrate "detail" and skip templating
    for i in template:
        if isinstance(template[i], dict) and len(template[i]) < 5:
            for j in template[i]:
                if isinstance(template[i][j], dict):
                    if inbound.get(i, {}).get(j):
                        extract = process.extractOne(
                            str(inbound[i][j]), list(template[i][j].keys())
                        )
                        print(extract)
                        if isinstance(inbound[i][j], (int, str)) and extract[1] > 85:
                            outbound[keys[c]] = extract[0]
                            c += 1
                else:
                    if inbound.get(i, {}).get(j) and isinstance(
                        inbound[i][j], (int, str)
                    ):
                        outbound[keys[c]] = str(inbound[i][j])
                        c += 1
        elif isinstance(template[i], list):
            if inbound.get(i):
                extract = process.extractOne(str(inbound[i]), list(template[i].keys()))
                print(extract)
                if isinstance(inbound[i], (int, str)) and extract[1] > 85:
                    outbound[keys[c]] = extract[0]
        else:
            if inbound.get(i):
                extract = process.extractOne(str(inbound[i]), list(template[i].keys()))
                print(extract)
                if isinstance(inbound[i], (int, str)) and extract[1] > 85:
                    outbound[keys[c]] = extract[0]
        c += 1
    # adjust page
    if (
        inbound.get("page")
        and str(inbound["page"]).isnumeric()
        and int(inbound["page"]) > 1
    ):
        outbound["action"] = "next"
        outbound["rec_start"] = str(str((int(inbound.get("page")) - 2) * 25))
    return outbound
    # for detail
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
# @catalog_bp.route("/classrooms") # make classroom endpoint
