import sys

from app import app

if __name__ == "__main__":
    debug = True if "--debug" in sys.argv else False
    app.run(debug=debug, host="0.0.0.0")
