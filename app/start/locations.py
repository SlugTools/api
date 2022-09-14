from pprint import pprint
from re import findall
from urllib.parse import parse_qs
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from httpx import Client
from thefuzz import fuzz

from app import readify


# TODO: loop @ 1 day
def scrape_locations(client):
    managed = {}
    page = client.get("https://nutrition.sa.ucsc.edu/")
    soup = BeautifulSoup(page.text, "lxml")
    # initial return setup; parses only from menu page
    for i in soup.find_all("a"):
        if "location" in i["href"]:
            managed[int(parse_qs(i["href"])["locationNum"][0])] = {
                # nutrition.sa.ucsc.edu
                "name": parse_qs(i["href"])["locationName"][0],
                # dining.ucsc.edu/eat
                "description": None,
                "location": None,  # TODO: turn into address
                "phone": None,
            }

    page = client.get("https://dining.ucsc.edu/eat/")
    soup = BeautifulSoup(page.text, "lxml")
    # groups headers and child elements (location info page)
    temp, matches = soup.find_all(["h2", "li"]), {}
    for index, value in enumerate(temp):
        if index + 1 < len(temp) and index - 1 >= 0:
            if temp[index - 1].name == "h2" and value.name == "li":
                matches[temp[index - 1]] = value

    # location matching
    for i in managed:
        ratio_list = {}
        isMultiple = [False, []]
        for j in matches:
            ratio = fuzz.ratio(
                managed[i]["name"].lower().replace("dining hall", ""),
                j.text.lower().replace("dining hall", ""),
            )
            ratio_list[ratio] = j
            if (
                managed[i]["name"].lower()[:-1] in j.text.lower()
                and "closed" not in j.text.lower()
            ):
                # FIXME: only serves perk coffee bars; try global approach
                if ratio == 52:  # detects for perk bar (phys sci building)
                    isMultiple[0] = True
                isMultiple[1].append(j)
        max_ratio = max(list(ratio_list.keys()))
        li = matches[ratio_list[max_ratio]]

        # location matching
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
            managed[i]["phone"] = readify(li.find("p").text.split("✆")[1])
            # TODO: scrape hours; probably a stretch since waitz reports it for dining halls
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
    soup = BeautifulSoup(page.text, "lxml")
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
