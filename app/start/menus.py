# from app import app # laod base url
from datetime import datetime
from urllib.parse import parse_qs
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from httpx import Client

from app import readify


# TODO: loop @ 1 day
def scrape_menus_items(client, locations, date=datetime.now().strftime("%m-%d-%Y")):
    client, master, itemsList = (
        Client(base_url="https://nutrition.sa.ucsc.edu/"),
        {},
        {},
    )
    for i in locations["managed"]:
        master[i] = {}
        for j in locations["managed"][i]:
            menu = {"short": {}, "long": {}}
            # short scraping
            link = f'shortmenu.aspx?locationNum={j:02d}&locationName={quote_plus(locations["managed"][i][j]["name"])}&naFlag=1&dtdate={date}'
            _, new = client.get(""), client.get(link)
            if new.status_code == 500:
                return None
            short_soup = BeautifulSoup(new.text, "lxml")
            status = short_soup.find("div", {"class": "shortmenuinstructs"})
            if status.text == "No Data Available":
                master[i][j] = None
                continue

            # long scraping
            items = {}
            for k in short_soup.find_all("a"):
                # TODO: do a faster check
                if k["href"].startswith("longmenu"):
                    new = client.get(k["href"])
                    long_soup = BeautifulSoup(new.text, "lxml")
                    meal = parse_qs(k["href"])["mealName"][0]
                    menu["long"][meal] = {}
                    for m in long_soup.find_all(
                        "div",
                        {
                            "class": [
                                "longmenucolmenucat",
                                "longmenucoldispname",
                                "longmenucolprice",
                            ]
                        },
                    ):
                        if m["class"][0] == "longmenucolmenucat":
                            menu["long"][meal][m.text.split("--")[1].strip()] = {}
                        elif m["class"][0] == "longmenucoldispname":
                            course = list(menu["long"][meal].keys())[-1]
                            item_id = m.find("input").attrs["value"]
                            menu["long"][meal][course][item_id] = readify(m.text)
                            items[item_id] = readify(m.text)
                        elif (
                            m.text.strip() != ""
                        ):  # else doesn't account for course row price whitespace
                            course = list(menu["long"][meal].keys())[-1]
                            item = list(menu["long"][meal][course].keys())[-1]
                            name_price = {
                                "name": menu["long"][meal][course][item],
                                "price": m.text,
                            }
                            menu["long"][meal][course][item] = name_price
                            items[item] = name_price

            # short scraping
            for k in short_soup.find_all(
                "div",
                {"class": ["shortmenumeals", "shortmenucats", ["shortmenurecipes"]]},
            ):  # meal(s), course(s), item(s)
                if k["class"][0] == "shortmenumeals":
                    menu["short"][k.text] = {}
                elif k["class"][0] == "shortmenucats":
                    menu["short"][list(menu["short"].keys())[-1]][
                        k.text.split("--")[1].strip()
                    ] = {}
                else:
                    meal = list(menu["short"].keys())[-1]
                    course = list(menu["short"][meal].keys())[-1]
                    # FIXME: ValueError: 'Cheese Sauce' is not in list
                    try:
                        menu["short"][meal][course][
                            list(items.keys())[
                                list(items.values()).index(readify(k.text))
                            ]
                        ] = readify(k.text)
                    except:
                        pass
            itemsList |= items
            # short and long menu attachment
            wipe = True
            for m in menu["short"]:
                if menu["short"][m]:
                    wipe = False
                else:
                    menu["short"][m] = None
            master[i][j] = None if wipe else menu
            # FIXME: clickable URL returns error because requires cache
            master[i][j] = {
                "name": locations["managed"][i][j]["name"],
                "link": str(client.base_url) + link,
            } | master[i][j]
    for i in master["butteries"]:
        if master["butteries"][i]:
            master["butteries"][i] = master["butteries"][i]["short"]
    return master, itemsList
