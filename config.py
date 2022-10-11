import os

from dotenv import load_dotenv


class Config:
    # FIXME: figure out dotenv
    load_dotenv()
    DETA_KEY = os.environ.get("DETA_KEY")
    SENTRY_SDK_DSN = os.environ.get("SENTRY_SDK_DSN")
    JSON_SORT_KEYS = False
