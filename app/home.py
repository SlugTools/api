from datetime import datetime
from flask import abort, Blueprint, render_template, request
from pprint import pprint

home_bp = Blueprint("home", __name__)

@home_bp.route('/')
def home():
    return render_template('home.html')