from aiohttp import ClientSession
from flask import Blueprint
from flask import request

laundry_bp = Blueprint("laundry", __name__)


@laundry_bp.route("/")
def home():
    return "<h1>Welcome to Laundry!</h1>"


@laundry_bp.route("/main")
async def main():
    async with ClientSession() as session:
        resp = await session.get(
            "https://www.laundryview.com/api/c_room?loc=9632", ssl=False
        )
        campus = await resp.json()
        final = {}
        for i in range(len(campus["room_data"])):
            id = campus["room_data"][i]["laundry_room_location"]
            resp = await session.get(
                f"https://www.laundryview.com/api/currentRoomData?location={id}",
                ssl=False,
            )
            location = await resp.json()
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
                    "washers": campus["num_available"][id].get("W")
                    if isValid
                    else None,
                },
                "summary": individual,
            }
    return final
