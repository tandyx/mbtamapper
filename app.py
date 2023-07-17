"""Main entry point for the application."""

import os
from threading import Thread
from dotenv import load_dotenv
from flask_app import FlaskApp
from gtfs_loader.feed import Feed

from shared_code.gtfs_helper_time_functions import get_date

load_dotenv()

if __name__ == "__main__":
    threads: list[Thread] = []
    for index, KEY in enumerate(os.getenv("LIST_KEYS").split(",")):
        app = FlaskApp(KEY, Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(-2)))
        thread = Thread(target=app.app.run, kwargs={"port": 5000 + index})
        threads.append(thread)
    for thread in threads:
        thread.start()

    # app = FlaskApp(
    #     "COMMUTER_RAIL", Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(-4))
    # )
    # app.app.run(debug=True, port=5002)
