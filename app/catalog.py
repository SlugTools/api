from datetime import datetime
from pprint import pprint
from re import compile
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request
from flask import url_for
from httpx import Client
from httpx import get
from httpx import post
from humanize import precisedelta
from orjson import loads
from thefuzz.process import extractOne

from app import camel_case
from app import catalogDB
from app import condense_args
from app import force_to_int
from app import parse_days_times
from app import readify

catalog = Blueprint("catalog", __name__)


@catalog.route("/")
def index():
    """Provides academically relative data for campus instructional offerings."""
    return redirect("/#catalog")


@catalog.route("/classroom/<string:name>", methods=["GET"])
def classroom(name: str):
    """Retrieve data for a classroom. Specify a classroom name with <code>name</code> (string)."""
    classrooms = catalogDB.get("classrooms")
    del classrooms["key"]
    res = extractOne(name, list(classrooms.keys()))
    # FIXME: adjust threshold
    _ = (
        True
        if compile(r"\d").search(name)
        else abort(
            400,
            "The argument <code>name</code> should contain numbers to indicate a specific room.",
        )
    )
    page = get(classrooms[res[0]]) if res[1] > 60 else abort(404)
    soup = BeautifulSoup(
        page.text,
        "lxml",
        parse_only=SoupStrainer("div", attrs={"class": "content contentBox"}),
    )
    titles, images = soup.find_all("h3"), []
    for i in soup.find_all("div", attrs={"class": "callout-right image"}):
        images.append(
            {
                "caption": readify(i.text.split(". ")[-1]),
                "link": f"https://its.ucsc.edu/classrooms/media-info/{i.find('img')['src']}",
            }
        )
    master = {
        "link": classrooms[res[0]],
        "capacity": int(titles[0].text.split(" ")[-1]),
        "facilityID": titles[1].text.split(": ")[-1],
        "equipment": [readify(i.text) for i in soup.find_all("li")],
        "notes": readify(
            " ".join([i.text for i in soup.find("ul").findNext(["p", "span"])])
        ),
        "images": images,
    }
    return master


@catalog.route("/teacher")
def teacher_to_home():
    return redirect("/#catalog-teacher")


# TODO: https://githrequestsub.com/Nobelz/RateMyProfessorAPI has a ~2s slower implementation; push a PR
# FIXME: fetch __ref from somewhere
# https://campusdirectory.ucsc.edu/cd_simple
@catalog.route("/teacher/<name>")
def teacher(name):
    """Retrieve public data for a registered university member."""
    # session = Session()
    # sid possibly prone to change
    page = get(
        f"https://www.ratemyprofessors.com/search/teachers?query={quote_plus(name)}&sid=1078"
    )
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("script"))
    content = {}

    for i in soup:
        if "_ = " in i.text:
            content = loads(i.text[: i.text.index(";")].split("_ = ")[1])
            # using first match at index 4 (relative to sid query argument)
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


@catalog.route("/term", methods=["GET", "POST"])
def term():
    """Retrieve a code for an academic term to use for a class/course search. Specify a quarter with <code>quarter</code> (string) and/or a year with <code>year</code> (integer)."""
    inbound = condense_args(request, True)
    year = int(datetime.now().strftime("%Y"))
    # TODO: fetch from calendar, currently hardcoded
    quarters, hold = {
        "winter": [datetime(year, 3, 24), 2],
        "spring": [datetime(year, 6, 15), 4],
        "summer": [datetime(year, 9, 1), 6],
        "fall": [datetime(year, 12, 9), 10],
    }, []
    if inbound.get("quarter"):
        if not quarters.get(inbound.get("quarter").lower()):
            abort(400)
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
    # code += 4 # TODO: figure out how pisa changes selected option
    return (
        {"code": code, "term": f"{year} {quarter.capitalize()} Quarter"}
        if code >= 2048
        else abort(400)
    )


@catalog.route("/class")
def class_to_home():
    return redirect("/#catalog-class")


# @catalog.route("/class/calendar", methods=["GET", "POST"])
# def class_calendar():
#     # TODO: times might override, make a check
#     # TODO: make a valid docstring
#     """Retrieve a generated calendar (<code>.ics</code> file) for specific class/course(s). Specify class/course numbers with <code>number</code> (array)."""
#     inbound, client = condense_args(request, True), Client()


@catalog.route("/class/detail", methods=["GET", "POST"])
@catalog.route("/course/detail", methods=["GET", "POST"])
def class_detail():
    """Retrieve details for a specific class/course. Specify a term with <code>term</code> (optional) and a number with <code>number</code>."""
    inbound, client = condense_args(request, True), Client()
    term = (
        inbound["term"]
        if inbound.get("term")
        else client.get(f"http://127.0.0.1:5000{url_for('catalog.term')}").json()[
            "code"
        ]
    )
    number = (
        str(inbound["number"])
        if inbound.get("number")
        else abort(400, "The argument <code>number</code> is required.")
    )
    outbound = {
        "action": "detail",
        "class_data[:STRM]": term,
        "class_data[:CLASS_NBR]": number,
    }
    page = post("https://pisa.ucsc.edu/class_search/index.php", data=outbound)
    soup = BeautifulSoup(
        page.text,
        "lxml",
        parse_only=SoupStrainer(
            "div", attrs={"class": ["col-xs-12", "col-xs-6", "panel panel-default row"]}
        ),
    )
    if soup.find("h2").text.strip() == "Class not found":
        abort(204)
    title = readify(soup.find("div", attrs={"class": "col-xs-12"}).text)
    links = soup.find_all("div", attrs={"class": "col-xs-6"})[1]
    master = {
        "header": {
            "title": {
                "subject": title.split(" ")[0],
                "number": title.split(" ")[1],
                "section": title.split(" ")[3],
                "name": " ".join(title.split(" ")[4:]),
            },
            "term": " ".join(
                readify(soup.find("div", attrs={"class": "col-xs-6"}).text).split(" ")[
                    :-1
                ]
            ),
            "links": {
                "detail": links.find("a")["href"],
                "textbooks": links.find_all("a")[1]["href"],
            },
        },
        "details": None,
        "description": None,
        "requirements": None,
        "notes": None,
        "meeting": None,
        "associatedSections": None,
    }
    # FIXME: detail doesn't follow header key
    for i in soup.find_all("div", attrs={"class": "panel panel-default row"}):
        section = i.find("h2").text
        if section == "Class Details":
            # details
            table, master["details"] = i.find_all(["dt", "dd"]), {}
            custom = {
                "Career": "career",
                "Grading": "grading",
                "Class Number": "number",
                "Type": "type",
                "Instruction Mode": "mode",
                "Credits": "credits",
                "General Education": "ge",
                "Status": "status",
            }
            for n, j in enumerate(table):
                if n < 16:
                    if j.name == "dt":
                        value = force_to_int(table[n + 1].text.strip())
                        master["details"][custom[j.text]] = (
                            value if str(value) else None
                        )
                else:
                    break
            master["details"] = master["details"] | {
                "capacity": {
                    "enrollment": {
                        "filled": int(table[21].text),
                        "total": int(table[19].text),
                    },
                    "waitlist": {
                        "filled": int(table[25].text),
                        "total": int(table[23].text),
                    },
                }
            }
            continue
        # TODO: combined sections
        # if i.find("h2").text == "Combined Sections":
        #     continue
        if section in ["Description", "Enrollment Requirements", "Class Notes"]:
            master[section.split(" ")[-1].lower()] = readify(
                i.find("div", attrs={"class": "panel-body"}).text
            )
            continue
        if section == "Meeting Information":
            comp = i.find_all("td")
            master["meeting"] = [] if len(comp) > 4 else {}
            # TODO: re-add duration for days and times?
            for j in range(0, len(comp), 4):
                daysTimes = (
                    parse_days_times(comp[j].text) if comp[j].text.strip() else None
                )
                # times and times | {"duration": precisedelta(datetime.strptime(times["end"], "%I:%M%p") - datetime.strptime(times["start"], "%I:%M%p"))}
                room = comp[j + 1].text.strip()
                dates = comp[j + 3].text.split(" - ")
                instance = {
                    "days": daysTimes["days"] if daysTimes else None,
                    "times": daysTimes["times"] if daysTimes else None,
                    "room": room if room else None,
                    "instructor": comp[j + 2].text.replace(",", ", "),
                    "dates": {
                        "start": dates[0],
                        "end": dates[1]
                        # "duration": precisedelta(datetime.strptime(dates[1], "%m/%d/%y") - datetime.strptime(dates[0], "%m/%d/%y"))
                    },
                }
                if isinstance(master["meeting"], dict):
                    master["meeting"] = instance
                    break
                master["meeting"].append(instance)
            continue
        if section == "Associated Discussion Sections or Labs":
            master["associatedSections"] = {}
            for j in soup.find_all("div", attrs={"class": "row row-striped"}):
                row = j.find_all("div", attrs={"class": "col-xs-6 col-sm-3"})
                head = row[0].text.split(" ")
                daysTimes = parse_days_times(row[1].text)
                master["associatedSections"][head[0][1:]] = {
                    "type": head[1],
                    "section": head[2],
                    "days": daysTimes["days"],
                    "times": daysTimes["times"],
                    "instructor": row[2].text.replace(",", ", ").strip(),
                    "location": row[3].text.split(": ")[1],  # might be None
                    "capacity": {
                        "enrollment": {
                            "filled": int(row[4].text.split(" ")[1]),
                            "total": int(row[4].text.split(" ")[3]),
                        },
                        "waitlist": {
                            "filled": int(row[5].text.split(" ")[1]),
                            "total": int(row[5].text.split(" ")[3]),
                        },
                    },
                    "status": row[6].text.strip(),
                }
    return master


# ~1.5s response time, speed up heavily
@catalog.route("/class/search", methods=["GET", "POST"])
@catalog.route("/course/search", methods=["GET", "POST"])
def class_search():
    f"""Retrieve class/course search results. Specify arguments (in their defined data type) accessible at <code><a href={url_for('catalog.class_search_template')}>{url_for('catalog.class_search_template')}</a></code>."""
    inbound = condense_args(request)
    # [curr year relative calendar, increment value]
    template = catalogDB.get("template")
    del template["key"]
    template = template if template else abort(503)
    outbound = catalogDB.get("outbound")
    del outbound["key"]
    c, keys = 0, list(outbound.keys())
    # TODO: abort with 500 for invalid types, or use default?
    # TODO: adjust ratio threshold for fuzzy matching
    # FIXME: operation keys not getting fuzzy matches properly
    # TODO: add debug option to view outbound headers
    # TODO: incorporate way to check type of courseNumber and courseUnits value
    # if it works, it works
    for i in template:
        if isinstance(template[i], dict):
            # compromise
            hasSubLevels = False
            for j in template[i]:
                if isinstance(template[i][j], dict):
                    hasSubLevels = True
                    break
            if hasSubLevels:
                for j in template[i]:
                    if isinstance(template[i][j], dict):
                        if inbound.get(i, {}).get(j):
                            extract = extractOne(
                                str(inbound[i][j]), list(template[i][j].keys())
                            )
                            if (
                                isinstance(inbound[i][j], (int, str))
                                and extract[1] > 85
                            ):
                                outbound[keys[c]] = extract[0]
                        c += 1
                    else:
                        if inbound.get(i, {}).get(j) and isinstance(
                            inbound[i][j], (int, str)
                        ):
                            outbound[keys[c]] = inbound[i][j]
                        c += 1
                continue  # debugging for a solid hour got me to add this line
            else:
                # special cases
                if isinstance(inbound.get(i), dict):
                    if i == "instructionModes":
                        for j in inbound[i]:
                            if not inbound[i][j]:
                                outbound[keys[c]] = ""
                    else:
                        # TODO: regulate # of results
                        if (
                            inbound[i].get("results")
                            and str(inbound[i]["results"]).isnumeric()
                        ):
                            outbound["rec_dur"] = inbound[i]["results"]
                        # TODO: regulate page #
                        if (
                            inbound[i].get("number")
                            and str(inbound[i]["number"]).isnumeric()
                            and int(inbound[i]["number"]) > 1
                        ):
                            outbound["action"] = "next"
                            outbound["rec_start"] = (
                                int(inbound[i]["number"]) - 2
                            ) * int(outbound["rec_dur"])
                elif inbound.get(i):
                    extract = extractOne(str(inbound[i]), list(template[i].keys()))
                    if isinstance(inbound[i], (int, str)) and extract[1] > 85:
                        outbound[keys[c]] = extract[0]
            c += 1
        elif isinstance(template[i], list):
            if inbound.get(i):
                extract = extractOne(str(inbound[i]), template[i])
                if isinstance(inbound[i], (int, str)) and extract[1] > 85:
                    outbound[keys[c]] = extract[0]
            c += 1
        else:
            if i in inbound:  # .get() issue
                # FIXME: type() is slower than isinstance()
                if isinstance(inbound[i], (int, str)):
                    outbound[keys[c]] = inbound[i]
            c += 1
    # workaround for https://github.com/deta/deta-python/issues/77
    new = outbound.copy()
    for i in outbound:
        new[i] = "" if outbound[i] == "default" else outbound[i]
    outbound, classes = new, {}
    page = post("https://pisa.ucsc.edu/class_search/index.php", data=outbound)
    soup = BeautifulSoup(
        page.text,
        "lxml",
        parse_only=SoupStrainer(
            "div", attrs={"class": ["panel panel-default row", "row hide-print"]}
        ),
    )
    for i in soup.find_all("div", attrs={"class": "panel panel-default row"}):
        head = readify(
            i.find("div", attrs={"class": "panel-heading panel-heading-custom"})
            .find("h2")
            .find("a")
            .text
        )
        body = i.find("div", attrs={"class": "panel-body"}).find("div")
        left = body.find_all("div", attrs={"class": "col-xs-6 col-sm-3"})
        right = body.find_all("div", attrs={"class": "col-xs-6 col-sm-6"})
        instructor = [
            i.strip()
            for i in left[1].get_text(separator="\n").replace(",", ", ").split("\n")
        ]  # FIXME: idk bout this
        typeLoc = right[0].text.split(" ")
        type, location = typeLoc[1].replace(":", ""), " ".join(typeLoc[2:])
        bottom = body.find_all("div", attrs={"class": "col-xs-6 col-sm-3 hide-print"})
        # FIXME: why is the first element empty
        daysTimes = (
            parse_days_times(right[1].text.strip()[right[1].text.index(": ") + 2 :])
            if "-" in right[1].text
            else None
        )
        # times and times | {"duration": precisedelta(datetime.strptime(times["end"], "%I:%M%p") - datetime.strptime(times["start"], "%I:%M%p"))}
        # TODO: status? (open, closed, waitlist)
        classes[int(left[0].find("a").text)] = {
            "title": {
                "subject": head.split(" ")[0],
                "number": head.split(" ")[1],
                "section": head.split(" ")[3],
                "name": " ".join(head.split(" ")[4:])
                .replace(":", ": ")
                .replace(",", ", "),
            },
            "link": left[0].find("a")["href"],
            "instructor": instructor[1:] if len(instructor) > 2 else instructor[1],
            "type": type if type else None,
            "location": location if location.strip() else None,
            "days": daysTimes["days"] if daysTimes else None,
            "times": daysTimes["times"] if daysTimes else None,
            "capacity": {
                "filled": int(left[2].text.split(" ")[1]),
                "total": int(left[2].text.split(" ")[3]),
            },
            "textbooks": bottom[0].find("a")["href"],  # link
            "mode": bottom[2].text.split(":")[1],
        }
    number = (
        1
        if int(outbound["rec_start"]) == 0
        else int(int(outbound["rec_start"]) / int(outbound["rec_dur"]) + 2)
    )
    total = int(
        soup.find("div", attrs={"class": "row hide-print"}).find_all("b")[2].text
    )
    left = total - int(outbound["rec_dur"]) * number
    display = left if left < int(outbound["rec_dur"]) else int(outbound["rec_dur"])
    display = total if total > display * total else display
    return {
        "page": {
            "number": number,
            "results": {"display": display, "total": total},
        },
        "classes": classes,
    }


@catalog.route("/class/search/template")
def class_search_template():
    f"""Retrieve the template to build your request for <a href='{url_for('catalog.class_search')}'>{url_for('catalog.class_search')}</a></code>."""
    template = catalogDB.get("template")
    del template["key"]
    return template if template else abort(503)


@catalog.route("/class/textbooks")
def forward_textbooks():
    return redirect("/#catalog-class-textbooks")


# TODO: use https://ucsc.textbookx.com/institutional/index.php?action=browse#/books/3426324
@catalog.route("/class/textbooks/<id>")
def get_textbooks(class_id):
    """Retrieve items/materials for a specific class/course number."""
    pass
