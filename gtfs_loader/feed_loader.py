"""FeedLoader class."""

import os
import time
import logging
from typing import NoReturn, Callable
from threading import Thread
import schedule

from sqlalchemy.exc import OperationalError
from .feed import Feed


class FeedLoader:
    """Loads GTFS data into map

    Args:
        feed (Feed): GTFS feed
        keys (list[str], optional): List of keys to load. Defaults to None.
    """

    GEOJSON_PATH = os.path.join(os.getcwd(), "static", "geojsons")

    def __init__(self, feed: Feed, keys: list[str] = None) -> None:
        self.feed = feed
        self.keys = keys or os.environ.get("LIST_KEYS").split(",")

    def __repr__(self) -> str:
        return f"<FeedLoader(feed={self.feed})>"

    def nightly_import(self) -> None:
        """Runs the nightly import."""
        self.feed.import_gtfs()
        self.feed.import_realtime()
        self.feed.purge_and_filter()

    def geojson_exports(self) -> None:
        """Exports geojsons."""
        self.feed.import_realtime()
        for key in self.keys:
            try:
                self.feed.export_geojsons(key, FeedLoader.GEOJSON_PATH)
            except OperationalError:
                logging.warning("OperationalError: %s", key)

    def update_realtime(self) -> None:
        """Updates realtime data.""" ""
        self.feed.import_realtime()
        logging.info("Updated realtime data.")

    def threader(self, func: Callable) -> None:
        """Threader function."""

        job_thread = Thread(target=func)
        job_thread.start()
        if func == self.update_realtime:  # pylint: disable=comparison-with-callable
            job_thread.join()

    def scheduler(self) -> NoReturn:
        """Schedules jobs."""
        schedule.every().second.do(self.threader, self.update_realtime)
        schedule.every(1.5).hours.at(":00").do(self.threader, self.geojson_exports)
        schedule.every().day.at("03:30", tz="America/New_York").do(
            self.threader, self.nightly_import
        )
        while True:
            schedule.run_pending()
            time.sleep(1)  # wait one minute
