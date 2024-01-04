from decimal import ROUND_HALF_UP, Decimal, localcontext
from re import findall, sub
from unicodedata import normalize


# TODO: remove lower option, conserve strict inbound header case sensitivity
def camel_case(text):
    snake = sub(r"(_|-)+", " ", text).title().replace(" ", "")
    return snake[0].lower() + snake[1:]


def condense_args(request, lower=False):
    inbound = {}
    try:
        inbound = request.get_json(force=True)
    except:
        pass
    inbound.update(dict(request.args))
    return {k.lower(): v for k, v in inbound.items()} if lower else inbound


def force_to_int(text):
    if any(c.isdigit() for c in text):
        return int(sub(r"\D", "", text))
    return text


# TODO: rework to reach all subkeys
# temp fix to conserve order while accessing NoSQL DB (forge/melt)
# con/de struct lexicographically sorted data


def forge(data):
    keys = list(data.keys())
    return {f"{(i + 1):02d}{keys[i]}": v[1] for i, v in enumerate(data.items())}


def melt(data):
    return {k[2:]: v for k, v in data.items() if k != "key"}


def parse_days_times(text):
    text = text.split(" ")
    days = {
        "M": "Monday",
        "Tu": "Tuesday",
        "W": "Wednesday",
        "Th": "Thursday",
        "F": "Friday",
        "Sa": "Saturday",
        "Su": "Sunday",
    }
    acros, times = findall("[A-Z][^A-Z]*", text[0]), text[1].split("-")
    {"start": times[0], "end": times[1]}
    return {
        "days": {i: days[i] for i in acros},
        "times": {"start": times[0], "end": times[1]},
    }


def readify(text):
    return sub(" +", " ", normalize("NFKD", text).replace("\n", "")).strip()


def rounder(num):
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        print(num)
        return Decimal(num).to_integral_value()
