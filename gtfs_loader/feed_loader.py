"""FeedLoader class."""
import logging
import os
import queue
import threading
import time
from typing import NoReturn

from schedule import Scheduler
from sqlalchemy.exc import OperationalError

from gtfs import Alert, Prediction, Vehicle
from helper_functions import get_current_time, get_date, timeit

from .feed import Feed


class FeedLoader(Scheduler):
    """Loads GTFS data into map

    Args:
        feed (Feed): GTFS feed
        keys (list[str], optional): List of keys to load. Defaults to None.
    """

    GEOJSON_PATH = os.path.join(os.getcwd(), "static", "geojsons")
    REALTIME_BINDINGS = (Alert, Vehicle, Prediction)

    def __init__(self, feed: Feed, keys_dict: dict[str, list[str]]) -> None:
        """Initializes FeedLoader.

        Args:
            feed (Feed): GTFS feed
            keys (list[str]): List of keys to load.
        """
        super().__init__()
        self.feed = feed
        self.keys_dict = keys_dict

    def __repr__(self) -> str:
        return f"<FeedLoader(feed={self.feed})>"

    def nightly_import(self) -> None:
        """Runs the nightly import."""
        self.feed.import_gtfs(chunksize=100000, dtype=object)
        for orm in FeedLoader.REALTIME_BINDINGS:
            self.feed.import_realtime(orm)
        self.feed.purge_and_filter(date=get_date())

    def geojson_exports(self) -> None:
        """Exports geojsons."""
        for key, routes in self.keys_dict.items():
            try:
                self.feed.export_geojsons(
                    key, routes, FeedLoader.GEOJSON_PATH, get_current_time()
                )
            except OperationalError:
                logging.warning("OperationalError: %s", key)

    @timeit
    def update_realtime(self, orm: Alert | Vehicle | Prediction) -> None:
        """Updates realtime data.

        Args:
            _orm (Alert | Vehicle | Prediction): ORM to update.
        """
        self.feed.import_realtime(orm)
        logging.info("Updated realtime data for %s.", orm.__tablename__)

    def run(self, timezone: str = "America/New_York") -> NoReturn:
        """Schedules jobs.

        Args:
            timezone (str, optional): Timezone. Defaults to "America/New_York".
        """
        logging.info("Starting scheduler")

        def worker_main():
            """Worker main function."""
            while True:
                job_func = jobqueue.get()
                if isinstance(job_func, tuple):
                    job_func[0](*job_func[1:])
                else:
                    job_func()
                jobqueue.task_done()

        jobqueue = queue.Queue()

        self.every(2).minutes.do(jobqueue.put, (self.update_realtime, Alert))
        self.every(12).seconds.do(jobqueue.put, (self.update_realtime, Vehicle))
        self.every().minute.do(jobqueue.put, (self.update_realtime, Prediction))
        self.every().day.at("04:00", tz=timezone).do(jobqueue.put, self.geojson_exports)
        self.every().day.at("03:30", tz=timezone).do(jobqueue.put, self.nightly_import)

        worker_thread = threading.Thread(target=worker_main)
        worker_thread.start()

        while True:
            self.run_pending()
            time.sleep(1)
