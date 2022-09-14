from bs4 import BeautifulSoup
from bs4 import SoupStrainer


def scrape_rooms(client):
    rooms, page = {}, client.get("https://its.ucsc.edu/classrooms/")
    soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer("select"))
    for i in soup.find_all("option")[1:]:
        rooms[i.text] = f"https://its.ucsc.edu{i['value']}"
    return rooms
