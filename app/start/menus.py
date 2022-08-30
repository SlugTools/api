# from app import app # laod base url
from datetime import datetime
from urllib.parse import parse_qs
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from httpx import Client

from .locations import scrape_locations
from app import readify


# TODO: loop @ 1 day
def scrape_menus(date=datetime.now().strftime("%m-%d-%Y")):
    client, locations, master = (
        Client(base_url="https://nutrition.sa.ucsc.edu/"),
        scrape_locations(),
        {},
    )
    for i in locations["managed"]:
        master[i] = {}
        for j in locations["managed"][i]:
            menu = {"short": {}, "long": {}}
            # short scraping
            _, new = client.get(""), client.get(
                f'shortmenu.aspx?locationNum={j:02d}&locationName={quote_plus(locations["managed"][i][j]["name"])}&naFlag=1&dtdate={date}'
            )
            if new.status_code == 500:
                return None
            short_soup = BeautifulSoup(new.text, "lxml")
            status = short_soup.find("div", {"class": "shortmenuinstructs"})
            if status.text == "No Data Available":
                master[i][j] = None
                continue

            # long scraping
            item_list = {}
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
                            menu["long"][meal][course][readify(m.text)] = item_id
                            item_list[readify(m.text)] = item_id
                        elif (
                            m.text.strip() != ""
                        ):  # else doesn't account for course row price whitespace
                            course = list(menu["long"][meal].keys())[-1]
                            item = list(menu["long"][meal][course].keys())[-1]
                            item_price = {
                                "id": menu["long"][meal][course][item],
                                "price": m.text,
                            }
                            menu["long"][meal][course][item] = item_price
                            item_list[item] = item_price

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
                    # FIXME: 'Cheese Pizza' KeyError; current fix is just a error bypass
                    # normalize() just removes the '\xa0' that comes at the end of each j.text
                    try:
                        menu["short"][meal][course][readify(k.text)] = item_list[
                            readify(k.text)
                        ]
                    except:
                        pass
            # short and long dict attachment
            master[i][j] = (
                None if all(not menu["short"][m] for m in menu["short"]) else menu
            )
    # remove submenus; short == long
    # parsing diningHalls and butteries separately not practical
    for i in master["butteries"]:
        if master["butteries"][i]:
            master["butteries"][i] = master["butteries"][i]["short"]
    return master


# imported from parent function
def get_menu(location_id: int, date):
    menus = scrape_menus(date)
    for i in menus:
        if location_id in list(menus[i].keys()):
            if menus[i][location_id]:
                return menus[i][location_id]
            else:
                # FIXME: return something that indicates an empty menu but valid location
                return {"short": None, "long": None}
