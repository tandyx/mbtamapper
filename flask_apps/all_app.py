"""This module is the entry point for the all_routes app. It creates the Flask app and loads the GTFS feed."""
from gtfs_loader.feed import Feed
from shared_code.gtfs_helper_time_functions import get_date
from .flask_app import FlaskApp

KEY = "ALL_ROUTES"
flask_app = FlaskApp(KEY, Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(-1)))
app = flask_app.app
