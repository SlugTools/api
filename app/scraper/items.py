import string
from re import findall
from re import sub
from unicodedata import normalize

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from requests import Session
from round_nutrition import Main


# process at request; consider making a db for all items (not efficient)
# sync with db and implement checks
# TODO: make contents federally compliant
def scrape_item(item_id: string):
    session = Session()
    url = session.get("https://nutrition.sa.ucsc.edu/")
    # location set to lowest int:02d; full content not displayed without locationNum query param
    url = session.get(
        f"https://nutrition.sa.ucsc.edu/label.aspx?locationNum=05&RecNumAndPort={item_id}"
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
    # FIXME: current bypass for 'Potassium' KeyError
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
        # TODO: keep as int, str, or add "kcal" unit?
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
