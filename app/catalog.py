from aiohttp import ClientSession
from bs4 import BeautifulSoup, SoupStrainer
from datetime import datetime
from flask import abort, Blueprint, request
from orjson import loads
from pprint import pprint
from requests import Session
from urllib.parse import quote_plus

catalog_bp = Blueprint("catalog", __name__)

@catalog_bp.route('/')
def home():
  return "<h1>Welcome to Catalog!</h1>"

# TODO: https://github.com/Nobelz/RateMyProfessorAPI has a ~2s slower implementation; push a PR
@catalog_bp.route('/teacher/<name>')
async def get_teacher(name):
    # session = Session()
    # sid possibly prone to change
    async with ClientSession() as session:
        page = await session.get(f'https://www.ratemyprofessors.com/search/teachers?query={quote_plus(name)}&sid=1078')
        soup = BeautifulSoup(await page.text(), 'lxml', parse_only = SoupStrainer('script'))
        content = {}
        
        for i in soup:
            if '_ = ' in i.text:
                content = loads(i.text[:i.text.index(';')].split('_ = ')[1])
                # using first match at index 4 (relative to sid query parameter)
                # if pushing pr to api library, access reference IDs to make list of teachers
                content = content[list(content.keys())[4]]
                for i in content:
                    if isinstance(content[i], int) and content[i] <= 0:
                        content[i] = None
                break
        
        # __ref possibly prone to change
        return {
            'name': f"{content['firstName']} {content['lastName']}",
            'department': content['department'],
            'rating': content['avgRating'],
            'ratings': content['numRatings'],
            'difficulty': content['avgDifficulty'],
            'wouldRetake': round(content['wouldTakeAgainPercent']) if content['wouldTakeAgainPercent'] else None,
            'page': f"https://www.ratemyprofessors.com/ShowRatings.jsp?tid={content['legacyId']}"
        } if 'id' in content and content['school']['__ref'] == 'U2Nob29sLTEwNzg=' else abort(404)

@catalog_bp.route('/class')
# /catalog/class?quarter=fall&year=2022&status=all&subject=MATH&courseName=name&courseNumber=number&courseKeyword=keyword&display=10
# term = #
# status = O (open), all (all classes)
# subject = codes
# courseName = name
# courseNumber = number
# courseKeyword = keyword
# instructorLastName = 
# display = 10 (default)

def get_course(name):
    if request.args.get('subject'):
        date = request.args.get('date')
    session = Session()
    year = int(datetime.now().strftime('%y'))
    # seems to be the pattern from 2013-2022
    # if not the case for the future, modify approach
    # season: month (week #) - month (week #)
    # fall: september (3) - december (2)
    # winter: january (1) - march (3)
    # spring: april (4) - june (2)
    # summer: july (4) - august (4)
    quarters, season = {
        "winter": [datetime(year, 3, 19), 2],
        "spring": [datetime(year, 6, 10), 2],
        "summer": [datetime(year, 8, 27), 2],
        "fall": [datetime(year, 12, 18), 4]
    }, 0
    for i in quarters:
        if datetime.today() <= quarters[i][0]:
            season += quarters[i][1]
    start = 2048 + ((22 - 5) * 10) + season
    data = {
        "action": "results",
        "binds[:term]": start,
        "binds[:reg_status]": "O",
        "binds[:subject]": "",
        "binds[:catalog_nbr_op]": "=",
        "binds[:catalog_nbr]": "",
        "binds[:title]": "",
        "binds[:instr_name_op]": "=",
        "binds[:instructor]": "",
        "binds[:ge]": "",
        "binds[:crse_units_op]": "=",
        "binds[:crse_units_from]": "",
        "binds[:crse_units_to]": "",
        "binds[:crse_units_exact]": "",
        "binds[:days]": "",
        "binds[:times]": "",
        "binds[:acad_career]": "",
        "binds[:asynch]": "A",
        "binds[:hybrid]": "H",
        "binds[:synch]": "S",
        "binds[:person]": "P",
        "rec_start": 0,
        "rec_dur": 10,
    }
    page = session.post(f'https://pisa.ucsc.edu/class_search/index.php', data=data)
    soup = BeautifulSoup(page.text, 'lxml')


    # api.slughub.com/food/locations
    # api.slughub.com/food/locations/<id>
    # api.slughub.com/food/menus/<id>
    # api.slughub.com/food/items/<id>

    # api.slughub.com/laundry/locations
    # api.slughub.com/class/<name>
    # api.slughub.com/professor/<name>