from httpx import Client


def update(id, client):
    location = client.get(f"currentRoomData?location={id}").json()
    summary = {"dryers": [], "washers": []}
    for i in location["objects"]:
        if i.get("appliance_type"):
            type = "dryers" if "dry" in i["type"].lower() else "washers"
            summary[type].append(
                {
                    "status": (
                        i["time_left_lite2"]
                        if i.get("time_left_lite2")
                        else i["time_left_lite"]
                    )
                }
            )
    return {"summary": summary}


def update_rooms(rooms):
    client = Client(base_url="https://www.laundryview.com/api")
    for i in rooms:
        rooms[i] |= update(i, client)
    return rooms


def update_rooms_id(id, rooms):
    client = Client(base_url="https://www.laundryview.com/api")
    return rooms[id] | update(id, client)
