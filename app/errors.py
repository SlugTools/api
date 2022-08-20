from flask import render_template

from app import app


# single file with one function
# might split later to accommodate all errors with different display funcs; test
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(429)
@app.errorhandler(500)
@app.errorhandler(503)
def internal_server_error(error):
    split = str(error).split(":")
    return (
        render_template("error.html", title=split[0], text=split[1].strip()),
        error.code,
    )
