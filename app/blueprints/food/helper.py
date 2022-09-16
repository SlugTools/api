from functools import partial
from re import findall
from re import sub
from unicodedata import normalize

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from flask import abort
from httpx import Client
from round_nutrition import Main
from thefuzz.process import extractOne


def update(live, compare):
    if live["isOpen"]:
        master = {
            "open": live["isOpen"],
            "occupation": {
                "capacity": {
                    "filled": live["people"],
                    "total": live["capacity"],
                },
                "busyness": {
                    "status": live["locHtml"]["summary"].split(" (")[0],
                    "percent": live["percentage"],
                },
            },
            "subLocation": None,
        }
        if live["subLocs"]:
            best, all = "", []
            for k in live["subLocs"]:
                # TODO: sync up bestLocation to match with subLoc's keys
                if k["id"] == live["bestLocations"][0]["id"]:
                    best = k["name"]
                # TODO: difference between isAvailable and isOpen?
                all.append(
                    {
                        "name": k["name"],
                        "abbreviation": k["abbreviation"],
                        "open": k["isOpen"],
                        "occupation": {
                            "capacity": {"filled": k["people"], "total": k["capacity"]},
                            "busyness": {
                                "status": k["subLocHtml"]["summary"].split(" (")[0],
                                "percent": k["percentage"],
                            },
                        },
                    }
                )
            master["subLocation"] = {"best": best, "list": all}
        trend = {}
        for k in compare["comparison"]:
            if k["valid"]:
                soup = BeautifulSoup(k["string"], "lxml")
                trend[k["trend"]] = soup.get_text()
        master["occupation"]["trend"] = trend if trend else None
        return master
    return {"open": False, "occupation": None, "subLocation": None}


def update_locations(locations):
    client = Client(base_url="https://waitz.io/")
    live = client.get("live/ucsc").json()["data"]
    compare = client.get("compare/ucsc").json()["data"]
    names = {i: j["name"] for i, j in enumerate(live)}
    for i in locations["managed"]["diningHalls"]:
        match = extractOne(locations["managed"]["diningHalls"][i]["name"], names)
        locations["managed"]["diningHalls"][i] |= update(
            live[match[2]], compare[match[2]]
        )
    return locations


def update_locations_id(locations, id):
    for i in locations["managed"]:
        for j in locations["managed"][i]:
            if j == str(id):
                if i == "diningHalls":
                    client = Client(base_url="https://waitz.io/")
                    live = client.get("live/ucsc").json()["data"]
                    compare = client.get("compare/ucsc").json()["data"]
                    names = {i: j["name"] for i, j in enumerate(live)}
                    match = extractOne(locations["managed"][i][j]["name"], names)
                    return locations["managed"][i][j] | update(
                        live[match[2]], compare[match[2]]
                    )

                return locations["managed"][i][j]
    return None


def round_comply(values):
    a = Main()
    functions = [
        a.calories,
        a.tot_fat,
        a.sat_fat,
        a.trans_fat,
        partial(a.cholesterol, minimal=True),
        a.sodium,
        partial(a.tot_carb, minimal=True),
        partial(a.dietary_fiber, minimal=True),
        partial(a.tot_sugars, minimal=True),
        partial(a.protein, minimal=True),
    ]
    return [f(v) for f, v in zip(functions, values)]


# TODO: simplify this
def scrape_item(id, comply=True):
    client = Client(base_url="https://nutrition.sa.ucsc.edu/")
    # location set to lowest int:02d; full content not displayed without locationNum argument
    _, url = client.get(""), client.get(f"label.aspx?locationNum=05&RecNumAndPort={id}")
    soup = BeautifulSoup(url.text, "lxml")
    if soup.find("div", {"class": "labelnotavailable"}):
        return None
    master = {
        "name": None,
        "ingredients": None,
        "labels": {
            "eggs": False,
            "vegan": False,
            "fish": False,
            "veggie": False,
            "gluten": False,
            "pork": False,
            "milk": False,
            "beef": False,
            "nuts": False,
            "halal": False,
            "soy": False,
            "shellfish": False,
            "treenut": False,
        },
        "nutrition": {
            "amounts": {
                "servingSize": None,
                "calories": None,
                "totalFat": None,
                "saturatedFat": None,
                "transFat": None,
                "cholesterol": None,
                "sodium": None,
                "totalCarbohydrate": None,
                "dietaryFiber": None,
                "totalSugars": None,
                "protein": None,
            },
            "percentDailyValues": {
                "totalFat": None,
                "saturatedFat": None,
                "cholesterol": None,
                "sodium": None,
                "totalCarbohydrate": None,
                "dietaryFiber": None,
                "vitaminD": None,
                "calcium": None,
                "iron": None,
                "potassium": None,
            },
        },
    }
    master["name"] = soup.find("div", {"class": "labelrecipe"}).text
    master["ingredients"] = soup.find("span", {"class": "labelingredientsvalue"}).text

    # labels
    for i in soup.find_all("img"):
        if i["src"].startswith("LegendImages"):
            master["labels"][i["src"].split("/", 1)[1][:-4]] = True

    # nutrition
    complete = ""
    soup = BeautifulSoup(url.text, "lxml", parse_only=SoupStrainer("tr"))
    for i in soup.find("td"):
        complete += sub(" +", " ", normalize("NFKD", i.text).replace("\n", "").strip())

    # TODO: hardcoded for now; maybe try to fetch keywords from scraped; might be a stretch
    keywords = [
        "Serving Size",
        "Calories",
        "Total Fat",
        "Sat. Fat",
        "Trans Fat",
        "Cholesterol",
        "Sodium ",
        "Tot. Carb.",
        "Dietary Fiber",
        "Sugars",
        "Protein",
        "Vitamin D - mcg",
        "Calcium",
        "Iron",
        "Potassium",
    ]
    for k in keywords:
        complete = sub(k, f"'{k}'", complete)

    pattern = rf"'({'|'.join(keywords)})'\s*([^'*]+)"
    matches = dict(findall(pattern, complete))
    matches = {k: v.strip() for k, v in matches.items()}
    # FIXME: current bypass for 'Potassium' KeyError; find alt
    for item in keywords:
        try:
            matches[item] = "0%" if not matches[item] else matches[item]
        except:
            matches[item] = "0%"

    for i, k in enumerate(master["nutrition"]["amounts"]):
        temp = matches[list(matches.keys())[i]]
        # fixed '- - -' value issue (example item id = 400387*2*01)
        temp = temp if any(i.isdigit() for i in temp) else f"0{temp.split()[-1]}"
        # currently int; switch to str or str + " kcal"?
        master["nutrition"]["amounts"][k] = temp

    for i, k in enumerate(master["nutrition"]["percentDailyValues"]):
        if i < 6:  # exclude vitaminD, calcium, iron, and potassium
            temp = master["nutrition"]["amounts"][k]
            temp = temp[temp.index("g") + 1 : len(temp) - 1]
            master["nutrition"]["percentDailyValues"][k] = int(temp) if temp else 0
        else:
            temp = matches[list(matches.keys())[i + 5]][:-1]
            master["nutrition"]["percentDailyValues"][k] = int(temp) if temp else 0

    for i in master["nutrition"]["amounts"]:
        temp = master["nutrition"]["amounts"][i]
        temp = temp[0 : temp.index("g") + 1] if str(temp).endswith("%") else temp
        master["nutrition"]["amounts"][i] = temp
    copy = list(master["nutrition"]["amounts"].values())

    if comply:
        copy = [copy[0]] + round_comply(copy[1:])

    for index, value in enumerate(copy):
        index = list(master["nutrition"]["amounts"].keys())[index]
        master["nutrition"]["amounts"][index] = value

    return master


def get_items_sum(inbound):
    ids = (
        list(inbound["ids"])
        if inbound.get("ids")
        else abort(400, "The argument <code>ids</code> is required.")
    )
    master = {}

    def search(s):
        return float(
            findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", str(s).strip())[
                0
            ]
        )

    for i in ids:
        if master:
            data = scrape_item(i, False)
            if not data:
                continue
            amts = list(master["amounts"].keys())
            master["amounts"]["servingSize"].append(
                data["nutrition"]["amounts"]["servingSize"]
            )

            for j, k in enumerate(master["percentDailyValues"]):
                hold = [
                    search(master["amounts"][amts[j + 1]]),
                    search(data["nutrition"]["amounts"][amts[j + 1]]),
                ]
                master["amounts"][
                    amts[j + 1]
                ] = f"{sum(hold)}{str(master['amounts'][amts[j + 1]]).replace(str(hold[0]), '')}"
                master["percentDailyValues"][k] += data["nutrition"][
                    "percentDailyValues"
                ][k]
            keys, copy = list(master["amounts"].keys()), list(
                master["amounts"].values()
            )
            copy = [copy[0]] + round_comply(copy[1:])
            for j, k in enumerate(copy):
                master["amounts"][keys[j]] = k
        else:
            data = scrape_item(i, False)
            if data:
                master = data["nutrition"]
                master["amounts"]["servingSize"] = [master["amounts"]["servingSize"]]
            else:
                continue
    return master if master else abort(204)
