"""FeedLoader class."""

import logging
import os
import queue
import threading
import time
from typing import NoReturn

from schedule import Scheduler

from gtfs_orms import Alert, Prediction, Vehicle
from helper_functions import get_date, timeit

from .feed import Feed


class FeedLoader(Scheduler, Feed):
    """Loads GTFS data into map

    Args:
        - `url (str)`: URL of GTFS feed
        - `keys_dict (dict[str, tuple[str]])`: Dictionary of keys to load
    """

    GEOJSON_PATH = os.path.join(os.getcwd(), "static", "geojsons")

    def __init__(self, url: str, keys_dict: dict[str, tuple[str]]) -> None:
        """Initializes FeedLoader.

        Args:
            - `url (str)`: URL of GTFS feed.
            - `keys_dict (dict[str, tuple[str]])`: Dictionary of keys to load.
        """
        Scheduler.__init__(self)
        Feed.__init__(self, url)
        self.url = url
        self.keys_dict = keys_dict

    @timeit
    def nightly_import(self) -> None:
        """Runs the nightly import."""
        self.import_gtfs(chunksize=100000, dtype=object)
        for orm in self.__class__.__realtime_orms__:
            self.import_realtime(orm)
        self.purge_and_filter(date=get_date())

    @timeit
    def geojson_exports(self) -> None:
        """Exports geojsons all geojsons listed in `cls.keys_dict`"""
        for key, routes in self.keys_dict.items():
            self.export_geojsons(key, routes, __class__.GEOJSON_PATH)

    def run(self, timezone: str = "America/New_York") -> NoReturn:
        """Schedules jobs.

        Args:
            - `timezone (str, optional)`: Timezone. Defaults to "America/New_York".
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

        self.every(2).minutes.do(jobqueue.put, (self.import_realtime, Alert))
        self.every(12).seconds.do(jobqueue.put, (self.import_realtime, Vehicle))
        self.every().minute.do(jobqueue.put, (self.import_realtime, Prediction))
        self.every().day.at("03:45", tz=timezone).do(jobqueue.put, self.geojson_exports)
        self.every().day.at("03:30", tz=timezone).do(jobqueue.put, self.nightly_import)

        worker_thread = threading.Thread(target=worker_main)
        worker_thread.start()

        while True:
            self.run_pending()
            time.sleep(1)
