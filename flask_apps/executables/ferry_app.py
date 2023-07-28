"""Ferry app for the ferry feed."""
from flask import Flask
from helper_functions import return_dirname
from .container import FEED, HOST
from .. import FlaskApp

KEY = "FERRY"
flask_app = FlaskApp(Flask(__name__, root_path=return_dirname(__file__, 3)), FEED, KEY)
app = flask_app.app

if __name__ == "__main__":
    app.run(debug=True, host=HOST, port=84)
