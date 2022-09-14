from http.client import HTTPException

from flask import current_app
from flask import render_template
from werkzeug.exceptions import Aborter


# TODO: forcibly render
class _204(HTTPException):
    code, name, description = (
        204,
        "No Content",
        "The client's request has succeeded but no content is to be returned.",
    )


current_app.aborter = Aborter(extra={204: _204})


@current_app.errorhandler(_204)  # no content (success)
@current_app.errorhandler(400)  # bad request
@current_app.errorhandler(404)  # not found
@current_app.errorhandler(405)  # method not allowed
@current_app.errorhandler(429)  # too many requests
@current_app.errorhandler(500)  # internal server error
@current_app.errorhandler(503)  # service unavailable
def internal_server_error(error):
    custom = {429: "The rate limit has been exceeded. Rate: "}
    return (
        render_template(
            "error.html",
            code=error.code,
            name=error.name,
            description=custom[error.code] + error.description
            if custom.get(error.code)
            else error.description,
        ),
        error.code,
    )
