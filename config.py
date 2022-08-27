import os

from dotenv import load_dotenv


class Config(object):
    # FIXME: swap name out for something else
    BASE_URL = "https://nutrition.sa.ucsc.edu/"
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    # FIXME: figure out dotenv
    load_dotenv()
    DETA_KEY = os.environ.get("DETA_KEY")
    SENTRY_SDK_DSN = os.environ.get("SENTRY_SDK_DSN")
    JSON_SORT_KEYS = False
    LOCATIONS_URL = "https://dining.ucsc.edu/eat/"
