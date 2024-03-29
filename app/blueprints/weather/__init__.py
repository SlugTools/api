from datetime import datetime, timedelta

import portolan
from flask import Blueprint, redirect, request
from pytz import UTC, timezone

from app import app, omw, rounder

bp = Blueprint("weather", __name__)
srcs = {"OpenWeather": "https://openweathermap.org"}


@bp.route("/")
def index():
    """Provides campus weather data."""
    return redirect(f"/#{request.blueprint}")


@bp.route("/current")
def current():
    """Retrieve current weather data"""

    data = omw.get(
        f"/data/2.5/weather?lat=36.99&lon=-122.06&units=imperial&appid={app.config['OPENWEATHER_KEY']}"
    ).json()
    a = datetime.fromtimestamp(int(data["sys"]["sunrise"]))
    b = datetime.fromtimestamp(int(data["sys"]["sunset"]))
    sunrise = a.astimezone(timezone("US/Pacific"))
    sunset = b.astimezone(timezone("US/Pacific"))

    return {
        "name": data["name"],
        "weather": data["weather"][0]["description"].title(),
        "cloudiness": f"{data['clouds']['all']}%",
        "temp": f"{rounder(data['main']['temp'])} °F",
        "humidity": f"{data['main']['humidity']}%",
        "wind": {
            "speed": f"{rounder(data['wind']['speed'])} mph",
            "dir": portolan.abbr(degree=data["wind"]["deg"]),
            "gust": f"{rounder(data['wind']['gust'])} mph",
        },
        "sunrise": sunrise.strftime("%-I:%M %p"),
        "sunset": sunset.strftime("%-I:%M %p"),
    }
