from flask import Blueprint
from flask import redirect
from flask import request
from httpx import Client

laundry = Blueprint("laundry", __name__)


@laundry.route("/")
def index():
    """Provides residential laundry facility data."""
    return redirect("/#laundry")


@laundry.route("/main")
def main():
    """Retrieve residential laundry facility data."""
    client = Client(base_url="https://www.laundryview.com/api")
    campus = client.get("c_room?loc=9632").json()
    final = {}
    for i in range(len(campus["room_data"])):
        id = campus["room_data"][i]["laundry_room_location"]
        location = client.get(f"currentRoomData?location={id}").json()
        individual = {"dryers": [], "washers": []}
        for k in location["objects"]:
            if k.get("appliance_type"):
                type = "dryers" if k["type"] == "dblDry" else "washers"
                individual[type].append(
                    {
                        "status": k["time_left_lite2"]
                        if k.get("time_left_lite2")
                        else k["time_left_lite"]
                    }
                )
        isValid = id in campus["num_available"]
        final[campus["room_data"][i]["laundry_room_name"]] = {
            "availability": {
                "dryers": campus["num_available"][id].get("D") if isValid else None,
                "washers": campus["num_available"][id].get("W") if isValid else None,
            },
            "summary": individual,
        }
    return final
