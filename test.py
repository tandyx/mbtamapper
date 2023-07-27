"""Test"""
import os
import logging
import time
from threading import Thread
from typing import NoReturn, Callable
from dotenv import load_dotenv
import schedule
from sqlalchemy.exc import OperationalError

# from sqlalchemy import select

from gtfs_loader import Feed

load_dotenv()


class FeedLoader:
    """Loads GTFS data into map

    Args:
        feed (Feed): GTFS feed"""

    def __init__(self, feed: Feed) -> None:
        self.feed = feed

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
        geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
        for key in os.getenv("LIST_KEYS").split(","):
            try:
                self.feed.export_geojsons(key, geojson_path)
            except OperationalError:
                logging.warning("OperationalError: %s", key)

    def update_realtime(self) -> None:
        """Updates realtime data.""" ""
        self.feed.import_realtime()
        logging.info("Updated realtime data:, %s", self.feed)

    def threader(self, func: Callable) -> None:
        """Threader function."""

        job_thread = Thread(target=func)
        job_thread.start()
        if func == self.update_realtime:  # pylint: disable=comparison-with-callable
            job_thread.join()

    def scheduler(self) -> NoReturn:
        """Schedules jobs."""
        schedule.every(5).seconds.do(self.threader, self.update_realtime)
        schedule.every().day.at("03:30", tz="America/New_York").do(
            self.threader, self.nightly_import
        )
        schedule.every().hour.at(":00", tz="America/New_York").do(
            self.threader, self.geojson_exports
        )
        # schedule.every().minute.at(":00", tz="America/New_York").do(
        #     self.threader, self.geojson_exports
        # )
        while True:
            schedule.run_pending()
            time.sleep(1)  # wait one minute


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed_obj = Feed(url="http://cdn.mbta.com/MBTA_GTFS.zip")
    fead_loader = FeedLoader(feed_obj)
    # fead_loader.nightly_import()
    # fead_loader.geojson_exports()
    fead_loader.scheduler()
