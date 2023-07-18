"""This module is the entry point for the all_routes app. It creates the Flask app and loads the GTFS feed."""
from flask import Flask
from shared_code.dirname import return_dirname
from ..flask_app import FlaskApp, feed


KEY = "ALL_ROUTES"
root_path = return_dirname(__file__, 3)
app = Flask(__name__, root_path=root_path)
flask_app = FlaskApp(app, feed, KEY)
