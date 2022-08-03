import os
from dotenv import load_dotenv

class Config(object):
    BASE_URL = 'https://nutrition.sa.ucsc.edu/'
    load_dotenv()
    DETA_KEY = os.environ.get("DETA_KEY")
    JSON_SORT_KEYS = False
    LOCATIONS_URL = 'https://dining.ucsc.edu/eat/'