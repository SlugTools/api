import os

from dotenv import load_dotenv


class Config:
    # FIXME: figure out dotenv
    load_dotenv()
    DETA_KEY = os.environ.get("DETA_KEY")
    OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY")
    SENTRY_DSN = os.environ.get("SENTRY_SDK_DSN")
    JSON_SORT_KEYS = False
