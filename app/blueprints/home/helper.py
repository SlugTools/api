from re import search

from app import app


def get_index():
    map, functions, rules = {}, app.view_functions, app.url_map.iter_rules()
    color, hold = {"GET": "forestgreen", "POST": "dodgerblue"}, []
    for i, j in zip(functions, rules):
        split = i.split(".")
        if "." in i and split[0] not in ["static", "home"]:
            if split[1] == "index":
                map[f"/{split[0]}"] = {
                    "description": functions[i].__doc__,
                    "routes": {},
                }
            elif functions[i].__doc__:
                route = f"/{'/'.join(str(j).split('/')[2:])}"
                dtype = search("<(.*):", route)
                default = True if dtype else False
                route = route.replace(f"{dtype.group(1)}:", "") if dtype else route
                methods = [
                    f"<p style='display:inline; color:{color[k]};'>{k}</p>"
                    for k in list(j.methods)
                    if k not in ["HEAD", "OPTIONS"]
                ]
                map[f"/{split[0]}"]["routes"][route] = {
                    "description": functions[i].__doc__.split(" E")[0],
                    "methods": " ".join(sorted(methods, reverse=True)),
                }
                map[f"/{split[0]}"]["routes"][route] |= (
                    {"default": functions[i].__doc__.split(": ")[1]} if default else {}
                )
                hold.append(i)
    return map


def get_sources():
    map, bps = {}, app.view_functions
    for i in bps:
        split = i.split(".")
        if "." in i and split[0] not in ["static", "home"]:
            if split[1] == "index":
                map[f"/{split[0]}"] = bps[i].__doc__
