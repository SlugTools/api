from flask import Blueprint, redirect, render_template
from httpx import get

weather = Blueprint("weather", __name__)
weather_sources = {"nothing": "yet"}


@weather.route("/")
def index():
    # req = get("https://wttr.in/Santa+Cruz?format=j1")
    return "in progress"
