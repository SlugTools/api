from datetime import datetime
from urllib.parse import parse_qs
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from httpx import Client
from thefuzz.process import extract

from app import readify


# TODO: task loop to run @ 12:00AM
# TODO: scraping everything on eat page, maybe isolate and target first two h2 elements
def scrape_locations(client):
    managed = {}
    page = client.get("https://nutrition.sa.ucsc.edu/")
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("a"))
    for i in soup:
        if "location" in i["href"]:
            managed[int(parse_qs(i["href"])["locationNum"][0])] = {
                # nutrition.sa.ucsc.edu
                "name": parse_qs(i["href"])["locationName"][0],
                # dining.ucsc.edu/eat
                "description": None,
                # TODO: turn into address
                "location": None,
                "phone": None,
            }

    page = client.get("https://dining.ucsc.edu/eat/")
    soup = BeautifulSoup(page.text, "lxml")
    temp, matches = soup.find_all(["h2", "li"]), {}
    for index, value in enumerate(temp):
        if index + 1 < len(temp) and index - 1 >= 0:
            if temp[index - 1].name == "h2" and value.name == "li":
                matches[temp[index - 1]] = value

    # match nutrition and dining page locations
    for i in managed:
        isMultiple = [False, []]
        match = extract(managed[i]["name"].lower(), list(matches.keys()), limit=2)
        if match[0][1] > match[1][1]:
            li = matches[match[0][0]]
        # FIXME: workaround for double perk locations, maybe tweak to accommodate any # of locations
        elif match[0][1] == match[1][1]:
            isMultiple[0] = True
            isMultiple[1] = [match[0][0], match[1][0]]
        else:
            li = matches[match[1][0]]

        if isMultiple[0]:
            if not isinstance(managed[i]["description"], list):
                managed[i]["description"] = []
                managed[i]["location"] = []
                managed[i]["phone"] = []
            for j in isMultiple[1]:
                managed[i]["description"].append(
                    readify(matches[j].find("p").text.split("✆")[0])
                )
                # TODO: use google maps places api to get address
                managed[i]["location"].append(
                    f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(j.text.strip())}"
                )
                managed[i]["phone"].append(
                    readify(matches[j].find("p").text.split("✆")[1])
                )
        else:
            managed[i]["description"] = readify(li.find("p").text.split("✆")[0])
            managed[i][
                "location"
            ] = f'https://www.google.com/maps/dir/?api=1&destination={quote_plus(managed[i]["name"])}'
            managed[i]["phone"] = (
                readify(li.find("p").text.split("✆")[1])[0:14] if li.find("p") else None
            )
            # TODO: scrape hours; probably a stretch since waitz reports status for dining halls
            # waitz mobile app shows hours; doesn't seem to be on the website/api

    # streetFood uses https://financial.ucsc.edu/Pages/Food_Trucks.aspx
    # unable to scrape through microsoft soap POST request
    # options like requests_html, html2pdf, pdfkit, etc. too heavy
    # FIXME: find non-intensive method of scraping streetFood
    # possible solutions:
    # - request data from a public repl hosting selenium scraping code
    # - try screenshot and ocring webpage on a loop
    # - try ratemyprof repo method, simple get requests
    unmanaged = {"streetFood": [], "other": []}
    page = client.get("https://basicneeds.ucsc.edu/resources/on-campus-food.html")
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer(["h3", "p", "ul"]))
    # groups headers and child elements (location info page)
    temp, matches = soup.find_all(["h3", "p", "ul"])[13:-5], {}
    for index, value in enumerate(temp):
        if value.name == "h3":
            matches[temp[index]] = []
        else:
            matches[list(matches.keys())[-1]].append(value)
    for k, v in matches.items():
        unmanaged["other"].append(
            {
                "name": k.text,
                # FIXME: description not properly punctuated; properly incorporate "\n" and whitepsace
                "description": readify("".join([i.text for i in v[2:]]))
                .strip()
                .replace("\n", " ")
                .replace("    ", ". "),
                "location": v[0].text[10:],
                "hours": v[1].text[7:],
            }
        )
    master = {
        # managed by UCSC Dining
        "managed": {"diningHalls": {}, "butteries": {}},
        # not managed by UCSC Dining
        "unmanaged": unmanaged,
    }
    for i in managed:
        master["managed"][
            "diningHalls" if "hall" in managed[i]["name"].lower() else "butteries"
        ][i] = managed[i]
    return master


# TODO: task loop to run @ 12:00AM
def scrape_menus_items(client, locations, date=datetime.now().strftime("%m-%d-%Y")):
    client, menus, items = (
        Client(base_url="https://nutrition.sa.ucsc.edu/"),
        {},
        {},
    )
    for i in locations["managed"]:
        menus[i] = {}
        for j in locations["managed"][i]:
            menu = {"short": {}, "long": {}}
            # short scraping
            link = f'shortmenu.aspx?locationNum={j:02d}&locationName={quote_plus(locations["managed"][i][j]["name"])}&naFlag=1&dtdate={date}'
            _, new = client.get(""), client.get(link)
            if new.status_code == 500:
                return None
            short_soup = BeautifulSoup(new.text, "lxml")
            status = short_soup.find("div", {"class": "shortmenuinstructs"})
            menus[i][j] = {
                "name": locations["managed"][i][j]["name"],
                "link": str(client.base_url) + link,
                "menu": None,
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
            if locations["managed"]["diningHalls"].get(j):
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
    for i in menus["butteries"]:
        if menus["butteries"][i] and menus["butteries"][i].get("short"):
            menus["butteries"][i]["menu"] = menus["butteries"][i].pop("long")
            del menus["butteries"][i]["short"]
            wipe = True
            for j in menus["butteries"][i]["menu"]:
                if menus["butteries"][i]["menu"][m]:
                    wipe = False
                else:
                    menus["butteries"][i]["menu"][m] = None
                if wipe:
                    menus["butteries"][i]["menu"] = None
    return menus, items
