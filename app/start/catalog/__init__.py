from bs4 import BeautifulSoup, NavigableString, SoupStrainer

from app import camel_case


def scrape_rooms(client):
    rooms, page = {}, client.get("https://its.ucsc.edu/classrooms/")
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("select"))
    for i in soup.find_all("option")[1:]:
        rooms[i.text] = f"https://its.ucsc.edu{i['value']}"
    return rooms


def scrape_headers(client):
    last, store, comp = (
        "",
        [],
        {"action": {"action": ["results", "detail"]}},  # next is adjusted by page
    )
    page = client.get("https://pisa.ucsc.edu/class_search/index.php")
    soup = BeautifulSoup(
        page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
    )
    # FIXME: GE top level key has weird escape chars
    for i in soup:
        if i.name == "label":
            camel = camel_case(i.text.strip())
            if i.get("class") == ["col-sm-2", "form-control-label"]:
                comp[camel], last = {}, camel
            elif i.get("class") == ["sr-only"]:
                comp[last]["input"] = ""
            elif i.find("input"):
                comp[camel] = {i.find("input")["name"]: i.find("input")["value"]}
        elif i.name == "select":
            options = {}
            for j in i:
                if isinstance(j, NavigableString):
                    continue
                options[j["value"]] = j.text
            comp[last][i["name"]] = options
            if "input" in comp[last]:
                del comp[last]["input"]
                store.append(last)
        elif i.name == "input" and i.get("type") == "text":
            comp[store[-1]][i["name"]] = ""
    # fill empty items with the last element of the last item
    last = ""
    for i in comp:
        if len(comp[i]) == 0:
            transfer = [list(comp[last].keys())[-1], list(comp[last].values())[-1]]
            del comp[last][transfer[0]]
            comp[i][transfer[0]] = transfer[1]
        last = i
    # workaround for https://github.com/deta/deta-python/issues/77
    for i in comp:
        for j in comp[i]:
            if isinstance(comp[i][j], dict):
                key = list(comp[i][j].keys())[0]
                if not key:
                    value = list(comp[i][j].values())[0]
                    comp[i][j] = {f"default-{key}": value} | comp[i][j]
                    del comp[i][j][key]
    return comp


# inB: user-readable headers (inbound)
# outB: site-readable headers (outbound; for POST req)
def build_headers(client):
    comp, inB = scrape_headers(client), {}
    print("done")
    print("building pisa headers...", end="", flush=True)
    for i in comp:
        if len(comp[i]) != 1:
            inB[i] = {}
            for j in comp[i]:
                if j[:-1].split("_")[-1] == "op":
                    inB[i]["operation"] = comp[i][j]
                elif j[:-1].split("_")[-1] == "nbr" or "_" not in j:
                    inB[i]["value"] = comp[i][j]
                else:
                    inB[i][j[:-1].split("_")[-1]] = comp[i][j]
        else:
            inB[i] = comp[i][list(comp[i].keys())[0]]
    modes = {}
    for i in list(inB.keys())[-4:]:
        modes[i] = True
        del inB[i]
    inB |= {"instructionModes": modes}
    inB["page"], outB = {"number": 1, "results": 25}, {}
    for i in comp:
        for j in comp[i]:
            if isinstance(comp[i][j], dict):
                outB[j] = list(comp[i][j].keys())[0]
            elif isinstance(comp[i][j], list):
                outB[j] = comp[i][j][0]
            else:
                outB[j] = comp[i][j]
    # TODO: adjust rec_dur
    outB["rec_start"], outB["rec_dur"] = "0", "25"
    if len(inB) == 2:
        inB, outB = None, None
    return inB, outB


# TODO: scrape instructional cal
def scrape_calendar(client):
    print("scraping calendar...", end="", flush=True)
    page = client.get("https://registrar.ucsc.edu/calendar/future.html")
    soup = BeautifulSoup(page.text, "lxml", SoupStrainer(["h3", "td"]))
    print("done")
    return soup
