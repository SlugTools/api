from datetime import datetime
from pprint import pprint
from random import randint
from urllib.parse import parse_qs, quote_plus

from bs4 import BeautifulSoup, SoupStrainer
from httpx import Client
from thefuzz.process import extract, extractOne

from app import readify

# TODO: periodic scraping


# TODO: scrape hours (hidden tags on page); maybe through Waitz (visible on mobile app)
# TODO: scrape street food (https://financial.ucsc.edu/Pages/Food_Trucks.aspx)
# TODO: scrape basic needs (https://basicneeds.ucsc.edu/food/on-campus-food.html)
# TODO: special case for UCen Bistro reservations (https://dining.ucsc.edu/university-center-bistro-cafe/index.html)
def scrape_locations(client):
    locs, ids = {}, []
    menu_site = "https://nutrition.sa.ucsc.edu/"
    page = client.get(menu_site).text
    soup = BeautifulSoup(page, "lxml", parse_only=SoupStrainer("a"))
    for i in soup:
        if "location" in i["href"]:
            params = parse_qs(i["href"])
            id = int(params["locationNum"][0])
            name = params["locationName"][0]
            ids.append(id)
            locs[params["locationName"][0]] = {
                "id": int(params["locationNum"][0]),
                "url": f"{menu_site}{i['href']}",
                "name": name,
                # if managed by UCSC
                "managed": True,
            }

    locs["University Center Cafe"] = locs.pop("UCen Coffee Bar")

    page = client.get("https://dining.ucsc.edu/eat/")
    soup = BeautifulSoup(page, "lxml")
    temp, matches = soup.find_all(["h2", "li", "table"]), {}

    # parse <li> tag (meta data of location)
    def meta(li):
        spl = li.find("p").text.split("✆")
        return {
            "description": readify(spl[0]),
            "iframe": li.find(
                "a", {"class": "btn btn-primary fancybox fancybox.iframe"}
            )["href"],
            "phone": readify(spl[1])[:14] if len(spl) > 1 else None,
        }

    # # just print tags of temp
    # for i in temp:
    #     print(i.name)
    #     print(i.text)

    # match b/w two sites
    for i, j in enumerate(temp):
        info = temp[i + 1]
        menuBtn = info.find("a", {"class": "btn btn-info"})
        # only proceed if more locations to iter through
        if j.name == "h2" and menuBtn:
            # print(j.text.strip())
            if menuBtn["href"] == menu_site:
                # direct match (dhs)
                locName = j.text.strip()
                # print(locName)
                if locs.get(locName):
                    locs[locName].update(meta(info))
                # fuzzy match (other)
                else:
                    # print(locName)
                    limit = " ".join(locName.split()[:3])
                    match = extractOne(limit, locs.keys())
                    print(limit, match)
                    # pprint(locs, sort_dicts=False)
                    # implement already added check
                    hold = locs[match[0]]
                    # print(hold, len(hold))
                    locs[locName] = {**hold, **meta(info)}
                    if len(hold) == 2:
                        del locs[match[0]]
            # not on ucsc menu site
            # cafe pdfs, and iveta
            else:
                # on god what am i doing
                # random id gen
                while True:
                    id = randint(10, 99)
                    if id not in locs.keys():
                        break

                url = info.find("a", {"class": "btn btn-info"})["href"]
                url = (
                    f"https://dining.ucsc.edu{url[2:]}" if url.startswith("..") else url
                )
                name = j.text.strip()
                locs[name] = {
                    "id": id,
                    "url": url,
                    "name": name,
                    "managed": False,
                    **meta(info),
                }
        if i == len(temp) - 2:
            break

    # pprint(locs)
    import json

    with open("app/start/food/new.json", "w") as f:
        json.dump(locs, f, indent=4)

    return locs

    # streetFood uses https://financial.ucsc.edu/Pages/Food_Trucks.aspx
    # unable to scrape through microsoft soap POST request
    # options like requests_html, html2pdf, pdfkit, etc. too heavy
    # FIXME: find non-intensive method of scraping streetFood
    # possible solutions:
    # - request data from a public repl hosting selenium scraping code
    # - try screenshot and ocring webpage on a loop
    # - try ratemyprof repo method, simple get requests

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


# TODO: task loop to run @ 12:00AM
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

            # short scraping
            if locs[i].get(j):
                for k in short_soup.find_all(
                    "div",
                    {
                        "class": [
                            "shortmenumeals",
                            "shortmenucats",
                            ["shortmenurecipes"],
                        ]
                    },
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
                                list(hold.keys())[
                                    list(hold.values()).index(readify(k.text))
                                ]
                            ] = readify(k.text)
                        except:
                            pass
            items |= hold
            # short and long menu attachment
            wipe = True
            for m in menu["short"]:
                if menu["short"][m]:
                    wipe = False
                else:
                    menu["short"][m] = None
            # FIXME: clickable URL returns error because requires base cache
            menus[i][j]["menu"] = None if wipe else menu
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
