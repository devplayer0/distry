from werkzeug.serving import run_simple

from . import app

run_simple('::', 8080, app)
