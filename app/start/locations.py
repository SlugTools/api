from re import findall
from urllib.parse import parse_qs
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from httpx import Client
from thefuzz import fuzz

from app import readify


# TODO: loop @ 1 day
# FIXME: fix porter market issue
def scrape_locations():
    client, managed = Client(), {}
    page = client.get("https://nutrition.sa.ucsc.edu/")
    soup = BeautifulSoup(page.text, "lxml")
    # initial return setup; parses only from menu page
    for i in soup.find_all("a"):
        if "location" in i["href"]:
            managed[int(parse_qs(i["href"])["locationNum"][0])] = {
                # nutrition.sa.ucsc.edu
                # 'id': int(parse_qs(i['href'])['locationNum'][0]),
                "name": parse_qs(i["href"])["locationName"][0],
                # dining.ucsc.edu/eat
                "description": None,
                "location": None,  # TODO: turn into address
                "phone": None,
                # 'hours': None,
                # waitz
                "open": None,  # include hours?
                "occupation": None,
            }

    page = client.get("https://dining.ucsc.edu/eat/")
    soup = BeautifulSoup(page.text, "lxml-xml")
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

        # waitz api processing
        data = client.get("https://waitz.io/live/ucsc").json()
        comp_data = client.get("https://waitz.io/compare/ucsc").json()
        ratio_list = {}
        for j in data["data"]:
            # current compromise to get past the name - ratio problem
            if len(ratio_list) == 4:
                break
            ratio = fuzz.ratio(
                managed[i]["name"].lower().replace("dining hall", ""),
                j["name"].lower().replace("dining hall", ""),
            )
            ratio_list[ratio] = [j, comp_data["data"][len(ratio_list)]]
        max_ratio = max(list(ratio_list.keys()))

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
                # https://developers.google.com/maps/documentation/urls/get-started; maybe parse web embed url
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
            # TODO: implement 'hours' scraping
            # resp = session.get(f'https://dining.ucsc.edu/eat/#{soup.find(li.find("a")["href"])}')
            # test = BeautifulSoup(resp.text, 'lxml')
            # print(test)

        # waitz matching
        # compromise in matching c9/c10 to c9/john r. lewis; contacted waitz support to change name
        # c9/c10 & c9/john r. lewis gives a ratio of 46, whereas others are 90+
        if max_ratio == 46 or max_ratio > 90:
            if ratio_list[max_ratio][0]["isOpen"]:
                managed[i]["open"] = True
                trends = []
                for j in ratio_list[max_ratio][1]["comparison"]:
                    if j["valid"]:
                        soup = BeautifulSoup(j["string"], "lxml")
                        text = soup.get_text()
                        trends.append(text)
                managed[i]["occupation"] = {
                    "people": ratio_list[max_ratio][0]["people"],
                    "capacity": ratio_list[max_ratio][0]["capacity"],
                    "busyness": {
                        "status": " ".join(
                            ratio_list[max_ratio][0]["locHtml"]["summary"].split(" ")[
                                :2
                            ]
                        ),
                        "percent": int(
                            findall(
                                r"\d+", ratio_list[max_ratio][0]["locHtml"]["summary"]
                            )[0]
                        ),
                    },
                    "bestLocation": None,
                    "subLocations": None,
                    "trends": None,
                }
                # if it works, it works
                if ratio_list[max_ratio][0]["bestLocations"]:
                    if ratio_list[max_ratio][0]["subLocs"]:
                        managed[i]["occupation"]["subLocations"] = []
                        for j in ratio_list[max_ratio][0]["subLocs"]:
                            if (
                                j["id"]
                                == ratio_list[max_ratio][0]["bestLocations"][0]["id"]
                            ):
                                managed[i]["occupation"]["bestLocation"] = j["name"]
                            managed[i]["occupation"]["subLocations"].append(
                                {
                                    "name": j["name"],
                                    "abbreviation": j["abbreviation"],
                                    "people": j["people"],
                                    "capacity": j["capacity"],
                                    "busyness": {
                                        "status": " ".join(
                                            j["subLocHtml"]["summary"].split(" ")[:2]
                                        ),
                                        "percent": int(
                                            findall(r"\d+", j["subLocHtml"]["summary"])[
                                                0
                                            ]
                                        ),
                                    },
                                }
                            )
                trends = []
                for j in ratio_list[max_ratio][1]["comparison"]:
                    if j["valid"]:
                        soup = BeautifulSoup(j["string"], "lxml")
                        trends.append(soup.get_text())
                managed[i]["occupation"]["trends"] = trends if trends else None
            else:
                managed[i]["open"] = False

    # streetFood uses https://financial.ucsc.edu/Pages/Food_Trucks.aspx
    # unable to scrape through soap POST request
    # options like requests_html, html2pdf, pdfkit, etc. not viable
    # FIXME: find non-intensive method of scraping streetFood
    # possible solutions:
    # - request data from public repl hosting selenium scraping code
    # - try screenshot and ocring webpage on a loop
    # try ratemyprof repo method, simple get requests
    unmanaged = {"streetFood": [], "other": []}
    page = client.get("https://financial.ucsc.edu/Pages/Food_Trucks.aspx")
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
