# from requests import Session
# session = Session()
# url = 'https://pisa.ucsc.edu/class_search/index.php'
# data = {
#     "action": "results",
#     "binds[:term]": "2228",
#     "binds[:reg_status]": "O",
#     "binds[:subject]": "",
#     "binds[:catalog_nbr_op]": "=",
#     "binds[:catalog_nbr]": "",
#     "binds[:title]": "",
#     "binds[:instr_name_op]": "=",
#     "binds[:instructor]": "",
#     "binds[:ge]": "",
#     "binds[:crse_units_op]": "=",
#     "binds[:crse_units_from]": "",
#     "binds[:crse_units_to]": "",
#     "binds[:crse_units_exact]": "",
#     "binds[:days]": "",
#     "binds[:times]": "",
#     "binds[:acad_career]": "",
#     "binds[:asynch]": "A",
#     "binds[:hybrid]": "H",
#     "binds[:synch]": "S",
#     "binds[:person]": "P"
# }
# x = session.post(url, data=data)
# from datetime import datetime
# from calendar import monthcalendar, setfirstweekday
# from numpy import array, where
# def week_of_month(year, month, day):
#     setfirstweekday(6)
#     x, b, e = array(monthcalendar(year, month)), 0, 0
#     print(x)
#     print(where(x==day))
#     for i in enumerate(x[0]):
#         if i[1] != 0:
#             b = i[0]
#             break
#     for i in enumerate(x[-1]):
#         if i[1] == 0:
#             e = i[0]
#             break
#     b = (7-b)/7
#     e = (7-e)/7 if x[where(x==day)[0][0]][0] == x[-1][0] else 7
#     print(b)
#     print(e)
#     # if where(x==day)[1][0] < 5:
#     #     return where(x==day)[0][0] - 1 + b + ((where(x==day)[1][0] + 1)/7) + e
#     return where(x==day)[0][0] - 2 + b + ((where(x==day)[1][0] + 1)/7) + e
# def week_of_month(year, month, day):
#     date_value, b = datetime.date(year, month, day), 0
#     setfirstweekday(6)
#     cal = monthcalendar(year, month)
#     # print(cal)
#     for i in enumerate(cal[0]):
#         if i[1] != 0:
#             b = i[0]
#             break
#     for i in enumerate(cal[-1]):
#         if i[1] == 0:
#             b += 7 - i[0]
#             break
#     # print(b)
#     r = date_value.isocalendar()[1] - date_value.replace(day=1).isocalendar()[1] + 1
#     return r
# # print(f"june ({week_of_month(2018, 6, 25)}) - august ({week_of_month(2018, 8, 31)})")
# # print(f"june ({week_of_month(2019, 6, 24)}) - august ({week_of_month(2019, 8, 30)})")
# # print(f"june ({week_of_month(2020, 6, 22)}) - august ({week_of_month(2020, 8, 28)})")
# print(f"march ({week_of_month(2021, 3, 28)}) - june ({week_of_month(2021, 6, 9)})")
# # print(f"june ({week_of_month(2022, 6, 20)}) - august ({week_of_month(2022, 8, 26)})")
# def wom(dt):
#         return dt.isocalendar()[1] - dt.replace(day=1).isocalendar()[1] + 1
#     # seems to be the pattern from 2013-2022
#     # if not the case for the future, modify approach
#     # season: month (week #) - month (week #)
#     # fall: september (3) - december (2)
#     # winter: january (1) - march (3)
#     # spring: april (4) - june (2)
#     # summer: july (4) - august (4)
# month = int(datetime.now().strftime('%m'))
# print(month)
# if month > 13:
#     print("fall")
#     season = 'fall'
# elif month < 9:
#     print("summer")
#     season = 'summer'
# elif month < 7:
#     print("spring")
#     season = 'summer' if wom(datetime.today()) == 5 else 'spring'
# elif month < 4:
#     print("winter")
#     season = 'spring' if wom(datetime.today()) == 5 else 'winter'
# print(season)
# from requests import Session
# session = Session()
# year = int(datetime.now().strftime('%y'))
# seems to be the pattern from 2013-2022
# if not the case for the future, modify approach
# season: month (week #) - month (week #)
# fall: september (3) - december (2)
# winter: january (1) - march (3)
# spring: april (4) - june (2)
# summer: july (4) - august (4)
# from pprint import pprint
# from bs4 import BeautifulSoup
# from bs4 import SoupStrainer
# from requests import get
# page = get("https://registrar.ucsc.edu/calendar/future.html")
# soup = BeautifulSoup(page.text, "lxml", parse_only=SoupStrainer(["h3", "td"]))
# calendar = dict.fromkeys(
#     [i for i in range(2020, 2031)],
#     {"fall": {}, "winter": {}, "spring": {}, "summer": {}},
# )
# pprint(calendar)
# quarter = ""
# for index, value in enumerate(soup.find_all(["h3", "td"])):
#     if value.name == "h3":
#         quarter = value.text.split()[0].lower()
#         print(quarter)
#     else:
#         print(value.attrs)
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import SoupStrainer
from requests import Session

session, opt = Session(), {}
page = session.get("https://pisa.ucsc.edu/class_search/index.php")
# FIXME: fix lxml parsing
soup = BeautifulSoup(
    page.text, "lxml", parse_only=SoupStrainer(["label", "select", "input"])
)
# with open('test.html', 'w') as f:
#     f.write(soup.prettify())
# for i in soup:
#     opt[i['name']] = {}
#     for j in i:
#         if isinstance(j, NavigableString):
#             continue
#         opt[i['name']][j['value']] = j.text


# from orjson import dumps
# obj = dumps(opt)
# with open("app/data.json", "wb") as f:
#     f.write(obj)
# print("done")
