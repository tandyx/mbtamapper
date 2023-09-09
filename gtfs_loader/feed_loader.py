"""FeedLoader class."""

import os
import time
import logging
from typing import NoReturn
from schedule import Scheduler
from sqlalchemy.exc import OperationalError

from gtfs import Alert, Vehicle, Prediction
from helper_functions import get_current_time, threader
from .feed import Feed


class FeedLoader(Scheduler):
    """Loads GTFS data into map

    Args:
        feed (Feed): GTFS feed
        keys (list[str], optional): List of keys to load. Defaults to None.
    """

    GEOJSON_PATH = os.path.join(os.getcwd(), "static", "geojsons")
    REALTIME_BINDINGS = [Alert, Vehicle, Prediction]

    def __init__(self, feed: Feed, keys: list[str] = None) -> None:
        """Initializes FeedLoader.

        Args:
            feed (Feed): GTFS feed
            keys (list[str], optional): List of keys to load. Defaults to None.
        """
        super().__init__()
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
                self.feed.export_geojsons(
                    key, FeedLoader.GEOJSON_PATH, get_current_time()
                )
            except OperationalError:
                logging.warning("OperationalError: %s", key)

    def update_realtime(self, _orm: Alert | Vehicle | Prediction = Prediction) -> None:
        """Updates realtime data.

        Args:
            _orm (Alert | Vehicle | Prediction, optional): ORM to update. Defaults to Prediction.
        """
        start = time.time()
        self.feed.import_realtime(_orm)
        logging.info(
            "Updated realtime data for %s in %s s.",
            _orm.__tablename__,
            round(time.time() - start, 4),
        )

    def run(self, timezone: str = "America/New_York") -> NoReturn:
        """Schedules jobs."""
        self.every(2).minutes.do(threader, self.update_realtime, True, Alert)
        self.every(12).seconds.do(threader, self.update_realtime, True, Vehicle)
        self.every().minute.do(threader, self.update_realtime, True, Prediction)
        # schedule.every().minute.do(self.threader, self.geojson_exports)
        # schedule.every(4).hours.at(":00").do(self.threader, self.geojson_exports)
        for times in ["04:00", "12:00", "20:00"]:
            self.every().day.at(times, tz=timezone).do(threader, self.geojson_exports)
        self.every().day.at("03:30", tz=timezone).do(threader, self.nightly_import)
        while True:
            self.run_pending()
            time.sleep(1)
