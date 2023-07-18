"""This module is the entry point for the subway app. It creates a Flask app and"""
from gtfs_loader.feed import Feed
from shared_code.gtfs_helper_time_functions import get_date
from .flask_app import FlaskApp  # pylint: disable=unable-to-import

KEY = "SUBWAY"
flask_app = FlaskApp(KEY, Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(-1)))
app = flask_app.app
