from pprint import pprint

from httpx import Client


def scrape_rooms(client):
    client = Client(base_url="https://www.laundryview.com/api")
    campus, rooms = client.get("c_room?loc=9632").json(), {}
    for i in campus["room_data"]:
        id = i["laundry_room_location"]
        rooms[id] = {
            "name": i["laundry_room_name"],
            "link": f"{str(client.base_url)}currentRoomData?location={id}",
            "data": None,
            "summary": None,
        }
        if campus["num_available"].get(id):
            d, w = campus["num_available"][id].get("D", 0), campus["num_available"][
                id
            ].get("W", 0)
            rooms[id] |= {
                "data": {
                    "online": i["online"],
                    "capacity": {"total": d + w, "dryers": d, "washers": w},
                }
            }
        location = client.get(f"currentRoomData?location={id}").json()
        summary = {"dryers": [], "washers": []}
        for i in location["objects"]:
            if i.get("appliance_type"):
                type = "dryers" if "dry" in i["type"].lower() else "washers"
                summary[type].append(
                    {
                        "status": i["time_left_lite2"]
                        if i.get("time_left_lite2")
                        else i["time_left_lite"]
                    }
                )
        summary["dryers"] = summary["dryers"] or None
        summary["washers"] = summary["washers"] or None
        rooms[id] |= {"summary": summary}
    return rooms
