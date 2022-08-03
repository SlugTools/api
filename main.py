from app import app
from os.environ import get

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = get('PORT'))