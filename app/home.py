from pprint import pprint

from flask import Blueprint
from flask import redirect
from flask import render_template

from app import app

home = Blueprint("home", __name__)


@home.route("/")
def index():
    map, functions, rules = {}, app.view_functions, app.url_map.iter_rules()
    color, hold = {"GET": "forestgreen", "POST": "dodgerblue"}, []
    for i, j in zip(functions, rules):
        # print(i)
        # print(j)
        # print()
        split = i.split(".")
        if "." in i and split[0] not in ["static", "home"]:
            if split[1] == "index":
                map[f"/{split[0]}"] = {
                    "description": functions[i].__doc__,
                    "routes": {},
                }
            elif functions[i].__doc__:
                route = f"/{'/'.join(str(j).split('/')[2:])}"
                methods = [
                    f"<p style='display:inline; color:{color[k]};'>{k}</p>"
                    for k in list(j.methods)
                    if k not in ["HEAD", "OPTIONS"]
                ]
                map[f"/{split[0]}"]["routes"][route] = {
                    "description": functions[i].__doc__,
                    "methods": ", ".join(methods),
                }
                hold.append(i)
    return render_template("index.html", map=map)
