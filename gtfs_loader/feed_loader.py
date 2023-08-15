"""FeedLoader class."""

import os
import time
import logging
from typing import NoReturn, Callable
from threading import Thread
import schedule

from gtfs_realtime import Vehicle, Prediction, Alert
from sqlalchemy.exc import OperationalError
from .feed import Feed


class FeedLoader:
    """Loads GTFS data into map

    Args:
        feed (Feed): GTFS feed
        keys (list[str], optional): List of keys to load. Defaults to None.
    """

    GEOJSON_PATH = os.path.join(os.getcwd(), "static", "geojsons")
    REALTIME_BINDINGS = [Alert, Vehicle, Prediction]

    def __init__(self, feed: Feed, keys: list[str] = None) -> None:
        self.feed = feed
        self.keys = keys or os.environ.get("LIST_KEYS").split(",")

    def __repr__(self) -> str:
        return f"<FeedLoader(feed={self.feed})>"

    def nightly_import(self) -> None:
        """Runs the nightly import."""
        self.feed.import_gtfs()
        for orm in FeedLoader.REALTIME_BINDINGS:
            self.feed.import_realtime(orm)
        self.feed.purge_and_filter()

    def geojson_exports(self) -> None:
        """Exports geojsons."""
        for key in self.keys:
            try:
                self.feed.export_geojsons(key, FeedLoader.GEOJSON_PATH)
            except OperationalError:
                logging.warning("OperationalError: %s", key)

    def update_realtime(self, _orm: Alert | Vehicle | Prediction = Prediction) -> None:
        """Updates realtime data.

        Args:
            _orm (Alert | Vehicle | Prediction, optional): ORM to update. Defaults to Prediction.
        """
        self.feed.import_realtime(_orm)
        logging.info("Updated realtime data for %s.", _orm.__tablename__)

    def threader(self, func: Callable, *args) -> None:
        """Threader function.

        Args:
            func (Callable): Function to thread.
            *args: Arguments for func.
        """

        job_thread = Thread(target=func, args=args)
        job_thread.start()
        if func == self.update_realtime:  # pylint: disable=comparison-with-callable
            job_thread.join()

    def scheduler(self) -> NoReturn:
        """Schedules jobs."""
        schedule.every(2).minutes.do(self.threader, self.update_realtime, Alert)
        schedule.every(12).seconds.do(self.threader, self.update_realtime, Vehicle)
        schedule.every().minute.do(self.threader, self.update_realtime, Prediction)
        # schedule.every().minute.do(self.threader, self.geojson_exports)
        schedule.every(2.5).hours.at(":00").do(self.threader, self.geojson_exports)
        schedule.every().day.at("03:30", tz="America/New_York").do(
            self.threader, self.nightly_import
        )
        while True:
            schedule.run_pending()
            time.sleep(1)  # wait one minute
