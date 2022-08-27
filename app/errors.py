from http.client import HTTPException

from flask import render_template
from werkzeug.exceptions import Aborter

from app import app


# TODO: split to provide custom messages?
class _204(HTTPException):
    code, name, description = (
        204,
        "No Content",
        "The client request has succeeded but no content is to be returned.",
    )


app.aborter = Aborter(extra={204: _204})


# forcibly render 204 (NoContent)
@app.errorhandler(_204)  # no content (success)
@app.errorhandler(400)  # bad request
@app.errorhandler(404)  # not found
@app.errorhandler(405)  # method not allowed
@app.errorhandler(429)  # too many requests
@app.errorhandler(500)  # internal server error
@app.errorhandler(503)  # service unavailable
def internal_server_error(error):
    return (
        render_template(
            "error.html",
            code=error.code,
            name=error.name,
            description=error.description,
        ),
        error.code,
    )
