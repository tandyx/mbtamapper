"""Main entry point for the application."""

import os
import logging
from dotenv import load_dotenv
from threading import Thread
from flask_apps.flask_app import FlaskApp
from gtfs_loader.feed import Feed

from shared_code.gtfs_helper_time_functions import get_date
from flask_apps import *

load_dotenv()
logging.getLogger().setLevel(logging.INFO)
DATE = get_date(-2)
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", DATE)
FLASK_APPS = [FlaskApp(key, FEED) for key in os.getenv("LIST_KEYS").split(",")]
THREADS = [
    Thread(target=app.run, kwargs={"port": 5000 + index})
    for index, app in enumerate(FLASK_APPS)
]

if __name__ == "__main__":
    for thread in THREADS:
        thread.start()
