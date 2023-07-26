"""Main entry point for the application."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

import os
import logging
from threading import Thread
from dotenv import load_dotenv
from flask import Flask
from flask_apps import FlaskApp
from gtfs_loader import Feed

from helper_functions import get_current_time

# from flask_apps import *

load_dotenv()
logging.getLogger().setLevel(logging.INFO)
DATE = get_current_time(-1)
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", DATE)

APPS = [
    FlaskApp(Flask(__name__), FEED, key) for key in os.getenv("LIST_KEYS").split(",")
]


if __name__ == "__main__":
    threads = [
        Thread(target=app.app.run, kwargs={"host": "0.0.0.0", "port": 80 + i})
        for i, app in enumerate(APPS)
    ]
    # "host": "0.0.0.0",
    for thread in threads:
        thread.start()

    # APPS[2].app.run(debug=True)
