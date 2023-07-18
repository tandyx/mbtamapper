"""Main entry point for the application."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

import os
import logging
from dotenv import load_dotenv
from threading import Thread
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from flask_apps.flask_app import FlaskApp
from gtfs_loader.feed import Feed

from shared_code.gtfs_helper_time_functions import get_date

# from flask_apps import *

load_dotenv()
logging.getLogger().setLevel(logging.INFO)
DATE = get_date(-2)
FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", DATE)
FLASK_APPS = [
    FlaskApp(Flask(__name__), FEED, key) for key in os.getenv("LIST_KEYS").split(",")
]

# app.wsgi_app = DispatcherMiddleware(
#     FLASK_APPS[0].app.wsgi_app, {f"/{app.key}": app.app.wsgi_app for app in FLASK_APPS}
# )

if __name__ == "__main__":
    threads = [
        Thread(target=app.run, kwargs={"port": 5000 + index})
        for index, app in enumerate(FLASK_APPS)
    ]
    for thread in threads:
        thread.start()
