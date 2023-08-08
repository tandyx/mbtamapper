"""Commuter Rail App"""
from flask import Flask
from helper_functions import return_dirname
from flask_apps.flask_app import FlaskApp
from .container import FEED, HOST, PORT

KEY = "COMMUTER_RAIL"
flask_app = FlaskApp(Flask(__name__, root_path=return_dirname(__file__, 3)), FEED, KEY)
app = flask_app.app

if __name__ == "__main__":
    app.run(debug=True, host=HOST, port=PORT + 2)
