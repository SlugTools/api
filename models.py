from app import db
from datetime import datetime

class Location(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String)
  description = db.Column(db.String)
  phone = db.Column(db.String)
  address = db.Column(db.String)
  open = db.Column(db.Boolean)
  occupation = db.relationship(db.String)