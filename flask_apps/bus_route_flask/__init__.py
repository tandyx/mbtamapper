"""This module is the entry point for the bus app. It creates a Flask app and"""
from flask import Flask
from shared_code.dirname import return_dirname
from ..flask_app import FlaskApp, feed


KEY = "BUS"
root_path = return_dirname(__file__, 3)
app = Flask(__name__, root_path=root_path)
flask_app = FlaskApp(app, feed, KEY)
