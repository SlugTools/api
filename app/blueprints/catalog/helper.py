from datetime import datetime
from itertools import islice
from re import compile
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, SoupStrainer
from flask import abort
from httpx import get, post
from orjson import loads
from thefuzz.process import extractOne

from app import currTerm, force_to_int, parse_days_times, readify


# TODO: add name
def get_rooms_name(name, rooms):
    res = extractOne(name, list(rooms.keys()))
    if not compile(r"\d").search(name):
        abort(
            400,
            "The argument 'name' should contain numbers to indicate a specific room.",
        )
    # FIXME: global threshold for extractOne has been 85, this one is more lenient
    page = get(rooms[res[0]], verify=False) if res[1] > 60 else abort(404)
    soup = BeautifulSoup(
        page.text,
        "lxml",
        parse_only=SoupStrainer("div", attrs={"class": "content contentBox"}),
    )
    titles, images = soup.find_all("h3"), []
    for i in soup.find_all("div", attrs={"class": "callout-right image"}):
        # TODO: set first image as main image?
        images.append(
            {
                "caption": readify(i.text.split(". ")[-1]),
                "link": f"https://its.ucsc.edu/classrooms/media-info/{i.find('img')['src']}",
            }
        )
    master = {
        "link": rooms[res[0]],
        "capacity": int(titles[0].text.split(" ")[-1]),
        "facilityID": titles[1].text.split(": ")[-1],
        "equipment": [readify(i.text) for i in soup.find_all("li")],
        "notes": readify(
            " ".join([i.text for i in soup.find("ul").findNext(["p", "span"])])
        ),
        "images": images,
    }
    return master


def get_ratings(name):
    # FIXME: sid possibly prone to change
    page = get(
        f"https://www.ratemyprofessors.com/search/professors/1078?q={quote_plus(name)}",
        verify=False,
    )
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("script"))

    for i in soup:
        tx = i.text
        if "_ = " in tx:
            pattern = compile(r"_ = ({.*?});")
            match = pattern.search(tx)
            content = loads(match.group(1))
            # using first match at index 4 (relative to sid query argument)
            # if pushing pr to api library, access reference IDs to make list of teachers
            content = next(islice(content.values(), 4, 5))
            for key, value in content.items():
                if isinstance(value, int) and value <= 0:
                    content[key] = None
            break

    return (
        {
            "name": f"{content['firstName']} {content['lastName']}",
            "department": content["department"].title().replace("And", "and"),
            "rating": content["avgRating"],
            "ratings": content["numRatings"],
            "difficulty": content["avgDifficulty"],
            # FIXME: wouldRetake displays null if 0%
            "wouldRetake": f"{round(content['wouldTakeAgainPercent'])}%"
            if content["wouldTakeAgainPercent"]
            else None,
            "url": f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={content['legacyId']}",
        }
        if "id" in content and content["school"]["__ref"] == "U2Nob29sLTEwNzg="
        else abort(404)
    )


def get_term(inbound):
    year = int(datetime.now().strftime("%Y"))
    # TODO: fetch from calendar, currently hardcoded
    quarters, hold = {
        "winter": 2,
        "spring": 4,
        "summer": 6,
        "fall": 10,
    }, []
    if inbound.get("quarter"):
        if not quarters.get(inbound["quarter"].lower()):
            abort(400)
        else:
            hold = [
                inbound["quarter"].lower(),
                quarters[inbound["quarter"].lower()],
            ]
    if inbound.get("year") and (
        int(inbound["year"]) - 1 <= year
    ):  # FIXME: pisa could list a year ahead, not sure
        year = int(inbound["year"])
    if not inbound.get("quarter"):
        spl = currTerm.split()
        year, hold = int(spl[0]), [spl[1], quarters[spl[1].lower()]]
    quarter, code = hold[0], 2048 + ((year % 100 - 5) * 10) + hold[1]
    # code += 4 # TODO: figure out how pisa changes selected option
    return (
        {"code": code, "term": f"{year} {quarter.capitalize()} Quarter"}
        if code >= 2048
        else abort(400)
    )


def get_classes(inbound):
    term = inbound["term"] if inbound.get("term") else get_term({})["code"]
    number = (
        str(inbound["number"])
        if inbound.get("number")
        else abort(400, "The argument 'number' is required.")
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
    title = abort(404) if title == "-" else title
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
            master["details"] |= {
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
                # daysTimes and daysTimes["times"] | {"duration": precisedelta(datetime.strptime(daysTimes["times"]["end"], "%I:%M%p") - datetime.strptime(daysTimes["times"]["start"], "%I:%M%p"))}
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


def get_classes_search(inbound, template, outbound):
    c, keys = 0, list(outbound.keys())
    # TODO: adjust ratio threshold for fuzzy matching
    # FIXME: operation keys not getting fuzzy matches properly
    # TODO: add debug argument to view outbound headers
    for i in template:
        if isinstance(template[i], dict):
            # compromise
            hasSubLevs = False
            for j in template[i]:
                if isinstance(template[i][j], dict):
                    hasSubLevs = True
                    break
            if hasSubLevs:
                # default to value parameter if no dictionary
                if isinstance(inbound.get(i), (int, str)):
                    # compromise for matching
                    matches = {
                        "courseNumber": "binds[:catalog_nbr]",
                        "courseUnits": "binds[:crse_units_exact]",
                        "instructorLastName": "binds[:instructor]",
                    }
                    if i in matches:
                        outbound[matches[i]] = str(inbound[i])
                    c += len(template[i])
                else:
                    for j in template[i]:
                        if isinstance(template[i][j], dict):
                            # FIXME: operation key not getting fuzzy matches properly
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
                continue
            else:
                # special cases
                if isinstance(inbound.get(i), dict):
                    if i == "instructionModes":
                        for j in inbound[i]:
                            if not inbound[i][j]:
                                outbound[keys[c]] = ""
                    # page
                    else:
                        # TODO: regulate # of results
                        if (
                            inbound[i].get("results", {}).get("display")
                            and str(inbound[i]["results"]["display"]).isnumeric()
                            and int(inbound[i]["results"]["display"]) <= 25
                        ):
                            outbound["rec_dur"] = inbound[i]["results"]["display"]
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
            if i in inbound and isinstance(inbound[i], (int, str)):
                outbound[keys[c]] = inbound[i]
            c += 1
    # workaround for https://github.com/deta/deta-python/issues/77
    new = outbound.copy()
    for i in outbound:
        elem = str(outbound[i])
        if elem.startswith("default"):
            split = elem.split("-")
            new[i] = split[1] if len(split) == 2 else ""
        else:
            new[i] = elem
    page = post("https://pisa.ucsc.edu/class_search/index.php", data=new)
    soup, classes = (
        BeautifulSoup(
            page.text,
            "lxml",
            parse_only=SoupStrainer(
                "div", attrs={"class": ["panel panel-default row", "row hide-print"]}
            ),
        ),
        {},
    )
    all_ = soup.find_all("div", attrs={"class": "panel panel-default row"})
    all_ = all_ if all_ else abort(404)
    for i in all_:
        head = i.find(
            "div", attrs={"class": "panel-heading panel-heading-custom"}
        ).find("h2")
        title = readify(head.find("a").text)
        body = i.find("div", attrs={"class": "panel-body"}).find("div")
        left = body.find_all("div", attrs={"class": "col-xs-6 col-sm-3"})
        right = body.find_all("div", attrs={"class": "col-xs-6 col-sm-6"})
        instructor = [
            i.strip()
            for i in left[1].get_text(separator="\n").replace(",", ", ").split("\n")
        ]
        typeLoc = right[0].text.split(" ")
        type, location = typeLoc[1].replace(":", ""), " ".join(typeLoc[2:])
        bottom = body.find_all("div", attrs={"class": "col-xs-6 col-sm-3 hide-print"})
        daysTimes = (
            parse_days_times(right[1].text.strip()[right[1].text.index(": ") + 2 :])
            if "-" in right[1].text
            else None
        )
        # times and times | {"duration": precisedelta(datetime.strptime(times["end"], "%I:%M%p") - datetime.strptime(times["start"], "%I:%M%p"))}
        classes[int(left[0].find("a").text)] = {
            "status": head.find("span").text,
            "title": {
                "subject": title.split(" ")[0],
                "number": title.split(" ")[1],
                "section": title.split(" ")[3],
                "name": " ".join(title.split(" ")[4:])
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
            "textbooks": bottom[0].find("a")["href"],
            "mode": bottom[2].text.split(":")[1],
        }
    number = (
        1
        if outbound["action"] == "results"
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
