"""Main entry point for the application."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

import os
import logging
from dotenv import load_dotenv
from threading import Thread
from flask import Flask, Blueprint
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from flask_apps import FlaskApp, BluePrintApp
from gtfs_loader import Feed

from helper_functions import get_date

# from flask_apps import *

load_dotenv()
logging.getLogger().setLevel(logging.INFO)
DATE = get_date(-2)
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", DATE)

APPS = [
    FlaskApp(Flask(__name__), FEED, key) for key in os.getenv("LIST_KEYS").split(",")
]


if __name__ == "__main__":
    threads = [
        Thread(target=app.app.run, kwargs={"host": "0.0.0.0", "port": 80 + i})
        for i, app in enumerate(APPS)
    ]

    for thread in threads:
        thread.start()

    # APPS[2].app.run(debug=True)
