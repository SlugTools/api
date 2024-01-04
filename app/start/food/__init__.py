import re
from datetime import datetime
from pprint import pprint
from random import randint
from urllib.parse import parse_qs, quote_plus, urlparse

from bs4 import BeautifulSoup, SoupStrainer
from httpx import Client
from thefuzz.process import extract, extractOne

from app import readify

# TODO: periodic scraping


# Google Maps Embed API URL to Google Maps URL
def embed_to_reg_url(embed):
    pattern_lat = re.compile(r"!2d(.*?)!")
    pattern_long = re.compile(r"!3d(.*?)!")
    pattern_place = re.compile(r"!2s(.*?)!")

    match_lat = pattern_lat.search(embed)
    match_long = pattern_long.search(embed)
    match_place = pattern_place.search(embed)

    lat = match_lat.group(1)
    long = match_long.group(1)
    place = match_place.group(1)

    # FIXME: workaround for UCen Bistro
    if lat[-3:] == "224":
        place = f"{place}%20Bistro"

    return f"https://www.google.com/maps?q={place}&ll={lat},{long}&z=15"


# dine site (all locations) = dining.ucsc.edu/eat
# nutrition site (managed locations) = nutrition.sa.ucsc.edu


# nutrition site
def build_managed_loc(menu_site, soup):
    locs = {}

    for i in soup:
        if "location" in i["href"]:
            params = parse_qs(i["href"])
            name = params["locationName"][0]
            locs[name] = {
                "id": int(params["locationNum"][0]),
                "url": f"{menu_site}{i['href']}",
                "name": name,
                "managed": True,
            }

    # FIXME: workaround for UCen Bistro / UCen Cafe
    cafe = "University Center Cafe"
    locs[cafe] = locs.pop("UCen Coffee Bar")
    locs[cafe]["name"] = cafe
    return locs


# dine site
def parse_location_meta(li):
    spl = li.find("p").text.split("✆")
    embed = li.find("a", {"class": "btn btn-primary fancybox fancybox.iframe"})["href"]
    return {
        "description": readify(spl[0]),
        "map": embed_to_reg_url(embed),
        "phone": readify(spl[1])[:14] if len(spl) > 1 else None,
    }


# dine site loc = nutrition site loc
def handle_direct_match(locs, name, info, menu_site):
    if locs.get(name):
        locs[name].update(parse_location_meta(info))
    else:
        handle_fuzzy_match(locs, name, info)


# dine site loc ≈ nutrition site loc
# or dine site subloc of nutrition site loc
# (e.g. Perk: PSB, E&M, etc.)
def handle_fuzzy_match(locs, name, info):
    limit = " ".join(name.split()[:3])
    match = extractOne(limit, locs.keys())

    hold = locs[match[0]]
    locs[name] = {**hold, **parse_location_meta(info)}
    locs[name]["name"] = name

    if len(hold) == 2:
        del locs[match[0]]


# dine site loc != nutrition site loc
def build_unmanaged_loc(locs, name, info):
    # gen random non-existing id
    while True:
        id = randint(10, 99)
        if id not in locs.keys():
            break

    url = info.find("a", {"class": "btn btn-info"})["href"]
    url = f"https://dining.ucsc.edu{url[2:]}" if url.startswith("..") else url

    locs[name] = {
        "id": id,
        "url": url,
        "name": name,
        "managed": False,
        **parse_location_meta(info),
    }


def extract_location_info(temp, locs, menu_site):
    for i, j in enumerate(temp):
        info = temp[i + 1]
        menuBtn = info.find("a", {"class": "btn btn-info"})

        if j.name == "h2" and menuBtn:
            name = j.text.strip()

            if menuBtn["href"] == menu_site:
                handle_direct_match(locs, name, info, menu_site)
            else:
                build_unmanaged_loc(locs, name, info)

        if i == len(temp) - 2:
            break


def scrape_locations(client):
    locs = {}
    menu_site = "https://nutrition.sa.ucsc.edu/"

    page = client.get(menu_site)
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("a"))
    locs = build_managed_loc(menu_site, soup)

    page = client.get("https://dining.ucsc.edu/eat/")
    soup = BeautifulSoup(page.text, "lxml")
    temp = soup.find_all(["h2", "li", "table"])

    extract_location_info(temp, locs, menu_site)

    return locs

    # unmanaged = {"streetFood": [], "other": []}
    # page = client.get("https://basicneeds.ucsc.edu/resources/on-campus-food.html")
    # soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer(["h3", "p", "ul"]))
    # # groups headers and child elements (location info page)
    # # FIXME: prone to change
    # temp, matches = soup.find_all(["h3", "p", "ul"])[17:-5], {}
    # for index, value in enumerate(temp):
    #     if value.name == "h3":
    #         matches[temp[index]] = []
    #     else:
    #         matches[list(matches.keys())[-1]].append(value)
    # for k, v in matches.items():
    #     unmanaged["other"].append(
    #         {
    #             "name": k.text,
    #             # FIXME: description not properly punctuated; properly incorporate "\n" and whitepsace
    #             "description": readify("".join([i.text for i in v[2:]]))
    #             .replace("\n", " ")
    #             .replace("    ", ". "),
    #             "location": v[0].text[10:],
    #             "hours": v[1].text[7:],
    #         }
    #     )
    # master = {
    #     # managed by UCSC Dining
    #     "managed": {"diningHalls": {}, "butteries": {}},
    #     # not managed by UCSC Dining
    #     "unmanaged": unmanaged,
    # }
    # for i in locs:
    #     master["managed"][
    #         "diningHalls" if "hall" in locs[i]["name"].lower() else "butteries"
    #     ][i] = locs[i]
    # return master


# TODO: optimize and break into smaller funcs for readability
def scrape_menus_items(client, locs, date=datetime.now().strftime("%m-%d-%Y")):
    client, menus, items = (
        Client(base_url="https://nutrition.sa.ucsc.edu/", verify=False),
        {},
        {},
    )
    for i in locs:
        menus[i] = {}
        if locs[i]["managed"]:
            menu = {"short": {}, "long": {}}
            # short scraping
            link = f"{locs[i]['url']}&dtdate={date}"
            _, new = client.get(""), client.get(link)
            if new.status_code == 500:
                return None
            short_soup = BeautifulSoup(new.text, "lxml")
            status = short_soup.find("div", {"class": "shortmenuinstructs"})
            menus[i] = {
                "id": locs[i]["id"],
                "url": locs[i]["url"],
                "name": locs[i]["name"],
                "managed": True,
                "data": None,
            }
            if status.text == "No Data Available":
                continue

            # long scraping
            hold = {}
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
                            hold[item_id] = readify(m.text)
                        elif m.text.strip() != "":
                            course = list(menu["long"][meal].keys())[-1]
                            item_id = list(menu["long"][meal][course].keys())[-1]
                            name_price = {
                                "name": menu["long"][meal][course][item_id],
                                "price": m.text,
                            }
                            menu["long"][meal][course][item_id] = name_price
                            hold[item_id] = name_price

            # # short scraping
            # if locs[i].get(j):
            #     for k in short_soup.find_all(
            #         "div",
            #         {
            #             "class": [
            #                 "shortmenumeals",
            #                 "shortmenucats",
            #                 ["shortmenurecipes"],
            #             ]
            #         },
            #     ):  # meal(s), course(s), item(s)
            #         if k["class"][0] == "shortmenumeals":
            #             menu["short"][k.text] = {}
            #         elif k["class"][0] == "shortmenucats":
            #             menu["short"][list(menu["short"].keys())[-1]][
            #                 k.text.split("--")[1].strip()
            #             ] = {}
            #         else:
            #             meal = list(menu["short"].keys())[-1]
            #             course = list(menu["short"][meal].keys())[-1]
            #             # FIXME: ValueError: 'Cheese Sauce' is not in list
            #             try:
            #                 menu["short"][meal][course][
            #                     list(hold.keys())[
            #                         list(hold.values()).index(readify(k.text))
            #                     ]
            #                 ] = readify(k.text)
            #             except:
            #                 pass
            # items |= hold
            # # short and long menu attachment
            # wipe = True
            # for m in menu["short"]:
            #     if menu["short"][m]:
            #         wipe = False
            #     else:
            #         menu["short"][m] = None
            # # FIXME: clickable URL returns error because requires base cache
            # menus[i][j]["menu"] = None if wipe else menu
    # for i in menus["butteries"]:
    #     if menus["butteries"][i] and menus["butteries"][i].get("short"):
    #         menus["butteries"][i]["menu"] = menus["butteries"][i].pop("long")
    #         del menus["butteries"][i]["short"]
    #         wipe = True
    #         for j in menus["butteries"][i]["menu"]:
    #             if menus["butteries"][i]["menu"][m]:
    #                 wipe = False
    #             else:
    #                 menus["butteries"][i]["menu"][m] = None
    #             if wipe:
    #                 menus["butteries"][i]["menu"] = None
    return menus, items
