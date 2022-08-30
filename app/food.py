from datetime import datetime
from re import findall
from re import sub
from unicodedata import normalize

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from flask import abort
from flask import Blueprint
from flask import redirect
from flask import request
from httpx import Client
from round_nutrition import Main

from app import foodDB

food = Blueprint("food", __name__)


@food.route("/")
def index():
    """Provides locational and nutritional data for on-campus food/eateries."""
    return redirect("/#food")


# TODO: update with waitz data upon request
@food.route("/locations")
def locations():
    """Get data for all on-campus dining/eatery locations."""
    # TODO: update waitz data
    locations = foodDB.get("locations")
    del locations["key"]
    return locations


@food.route("/locations/<int:id>")
def import_location(id: int):
    """Get today's locational data for an on-campus dining/eatery location."""
    # TODO: update waitz data
    locations = foodDB.get("locations")
    del locations["key"]
    for i in locations["managed"]:
        for j in locations["managed"][i]:
            if j == str(id):
                return locations["managed"][i][j]
    abort(204)


@food.route("/menus", methods=["GET"])
def menus():
    """Get today's menu data for all on-campus and university-managed dining/eatery locations"""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    # TODO: implement different day menus
    menus = foodDB.get("menus")
    del menus["key"]
    return menus


@food.route("/menus/<int:id>")
def menu(id: int):
    """Get today's menu data for an on-campus and university-managed dining/eatery location."""  # Specify a date with <code>date</code> in the <code>MM-DD-YY</code> format."""
    # TODO: implement different day menus
    menus = foodDB.get("menus")
    del menus["key"]
    for i in menus:
        for j in menus[i]:
            if j == str(id):
                return menus[i][j] if menus[i][j] else abort(204)
    abort(204)


def scrape_item(id):
    client = Client(base_url="https://nutrition.sa.ucsc.edu/")
    # location set to lowest int:02d; full content not displayed without locationNum query param
    _, url = client.get(""), client.get(
        f"https://nutrition.sa.ucsc.edu/label.aspx?locationNum=05&RecNumAndPort={id}"
    )
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
            "amountPerServing": {
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
            "percentDailyValue": {
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
    copy = {}
    for item in keywords:
        try:
            copy[item] = "0%" if not matches[item] else matches[item]
        except:
            copy[item] = "0%"
    matches = copy
    # matches['Serving Size'] = search('ize (.*?)Cal', original).group(1).replace('%', '/')

    for index, key in enumerate(master["nutrition"]["amountPerServing"]):
        temp = matches[list(matches.keys())[index]]
        # fixed '- - -' value issue (example item id = 400387*2*01)
        temp = temp if any(i.isdigit() for i in temp) else f"0{temp.split()[-1]}"
        # currently int; switch to str or str + " kcal"?
        master["nutrition"]["amountPerServing"][key] = (
            temp if key != "calories" else int(temp)
        )

    for index, key in enumerate(master["nutrition"]["percentDailyValue"]):
        if index < 6:  # exclude vitaminD, calcium, iron, and potassium
            temp = master["nutrition"]["amountPerServing"][key]
            temp = temp[temp.index("g") + 1 : len(temp) - 1]
            master["nutrition"]["percentDailyValue"][key] = int(temp) if temp else 0
        else:
            temp = matches[list(matches.keys())[index + 5]][:-1]
            master["nutrition"]["percentDailyValue"][key] = int(temp) if temp else 0

    for i in master["nutrition"]["amountPerServing"]:
        temp = master["nutrition"]["amountPerServing"][i]
        temp = temp[0 : temp.index("g") + 1] if str(temp).endswith("%") else temp
        master["nutrition"]["amountPerServing"][i] = temp
    copy = list(master["nutrition"]["amountPerServing"].values())

    # round for federal compliance
    a = Main()
    copy[1] = a.calories(copy[1])
    copy[2] = a.tot_fat(copy[2])
    copy[3] = a.sat_fat(copy[3])
    copy[4] = a.trans_fat(copy[4])
    copy[5] = a.cholesterol(copy[5])
    copy[6] = a.sodium(copy[6])
    copy[7] = a.tot_carb(copy[7])
    copy[8] = a.dietary_fiber(copy[8])
    copy[9] = a.tot_sugars(copy[9])
    copy[10] = a.protein(copy[10])

    for index, value in enumerate(copy):
        index = list(master["nutrition"]["amountPerServing"].keys())[index]
        master["nutrition"]["amountPerServing"][index] = value

    return master


@food.route("/items")
def items_to_home():
    return redirect("/#food-items")


@food.route("/items/<id>")
def items(id):
    """Get nutritional data for a on-campus university-managed dining/eatery location."""
    response = scrape_item(id)
    return response if response else abort(204)


# account for item IDs with fractional servings
@food.route("/items/<id_1>/<id_2>")
def items_frac_serving(id_1, id_2):
    response = scrape_item(f"{id_1}/{id_2}")
    return response if response else abort(404)
