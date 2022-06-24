from datetime import datetime
from flask import abort, Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# import flask_monitoringdashboard as dashboard
from scraper import *
import os

limit = "5 per minute"
app = Flask(__name__, template_folder = "templates")
limiter = Limiter(
  app,
  key_func = get_remote_address,
  default_limits = [limit],
)
app.config['JSON_SORT_KEYS'] = False # @hdadhich01
# app.config['SERVER_NAME'] = "localhost:5000"
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///locations.db"
# db = SQLAlchemy(app)
# dashboard.config.init_from(file='/C:\\Users\\hdadh\\Desktop\\FlaskApp/config.cfg')

# TODO: get both url and query parameters working for each route
# FIXME: types for all parameters, route functions, and call functions
# TODO: find way to preload base site cookies without including get statement in each function

@app.route("/")
def home():
  return render_template("api_home.html")

# @app.route("/favicon.ico")
# def favicon():
#   return "https://pbs.twimg.com/profile_images/539512753677815808/UGmYRvvW_400x400.png"

@app.route("/locations", subdomain = "api")
def import_locations():
  return get_locations()

@app.route("/locations/<int:location_id>")
def import_location(location_id: int):
  response = get_location(int(f"{location_id:02d}"))
  return response if response else abort(400)

@app.route("/menus", subdomain = "api")
def import_menus():
  date = datetime.now().strftime("%m-%d-%Y")
  if request.args.get("date"):
    date = request.args.get("date")
  response = get_menus(date)
  return response if response else abort(400)

@app.route("/menus/<int:location_id>", subdomain = "api")
def import_menu(location_id: int):
  date = datetime.now().strftime("%m-%d-%Y")
  if request.args.get("date"):
    date = request.args.get("date")
  response = get_menu(int(f"{location_id:02d}"), date)
  return response if response else abort(400)

@app.route("/items/<item_id>", subdomain = "api")
def import_item(item_id):
  response = get_item(item_id)
  return response if response else abort(400)

@app.route("/items/<item_id1>/<item_id2>", subdomain = "api")
def import_fraction_item(item_id1, item_id2):
  response = get_item(f"{item_id1}/{item_id2}")
  return response if response else abort(400)

@app.errorhandler(400)
def bad_request(error):
  split = str(error).split(":")
  return render_template("error.html", title = split[0], text = split[1].strip()), 400

@app.errorhandler(404)
def not_found(error):
  split = str(error).split(":")
  return render_template("error.html", title = split[0], text = split[1].strip()), 404

@app.errorhandler(429)
def too_many_requests(error):
  split = str(error).split(":")
  return render_template("error.html", title = split[0], text = f"Rate Limit: {limit}"), 429

@app.errorhandler(500)
def internal_server_error(error):
  split = str(error).split(":")
  return render_template("error.html", title = split[0], text = split[1].strip()), 500

if __name__ == "__main__":
  app.run(debug = True, host = "0.0.0.0", port = os.environ.get("PORT"))