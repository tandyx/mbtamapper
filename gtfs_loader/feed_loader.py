"""FeedLoader class."""

import logging
import os
import time
from threading import Thread
from typing import Callable, NoReturn

from schedule import Scheduler

from gtfs_orms import Alert, Prediction, Vehicle
from helper_functions import get_date, timeit

from .feed import Feed


class FeedLoader(Scheduler, Feed):
    """Loads GTFS data into map \
        and schedules jobs to import realtime data.

    Args:
        - `url (str)`: URL of GTFS feed
        - `geojson_path (str)`: Path to save geojsons
        - `keys_dict (dict[str, list[str]])`: Dictionary of keys to load
        - `**kwargs`: Keyword arguments to pass to `Feed`, such as `gtfs_name`
    """

    def __init__(
        self, url: str, geojson_path: str, keys_dict: dict[str, list[str]], **kwargs
    ) -> None:
        """Initializes FeedLoader.

        Args:
            - `url (str)`: URL of GTFS feed.
            - `geojson_path (str)`: Path to save geojsons.
            - `keys_dict (dict[str, list[str]])`: Dictionary of keys to load.
            - `**kwargs`: Keyword arguments to pass to `Feed`, such as `gtfs_name`.
        """
        Scheduler.__init__(self)
        Feed.__init__(self, url, **kwargs)
        self.url = url
        self.keys_dict = keys_dict
        self.geojson_path = geojson_path

    @timeit
    def nightly_import(self, **kwargs) -> None:
        """Runs the nightly import.

        args:
            - `**kwargs`: keyword arguments to pass to `import_gtfs`.\n
        """
        self.import_gtfs(chunksize=100000, dtype=object, **kwargs)
        for orm in self.__class__.REALTIME_ORMS:
            self.import_realtime(orm)
        self.purge_and_filter(date=get_date())

    @timeit
    def geojson_exports(self) -> None:
        """Exports geojsons all geojsons listed in `self.keys_dict`"""
        for key, routes in self.keys_dict.items():
            self.export_geojsons(key, *routes, file_path=self.geojson_path)

    def import_and_run(
        self, import_data: bool = False, timezone: str = "America/New_York", **kwargs
    ) -> NoReturn:
        """this is the main entrypoint for the application.

        Args:
            - `import_data (bool, optional)`: reloads the database and geojsons.\
                Defaults to False.
            - `timezone (str, optional)`: Timezone. Defaults to "America/New_York".
            - `**kwargs`: Keyword arguments to pass to `nightly import`.
        """

        if import_data or not os.path.exists(self.db_path):
            self.nightly_import(**kwargs)
        if import_data or not os.path.exists(self.geojson_path):
            self.geojson_exports()
        self.run(timezone=timezone)

    def run(self, timezone: str = "America/New_York") -> NoReturn:
        """Schedules jobs.

        Args:
            - `timezone (str, optional)`: Timezone. Defaults to "America/New_York".
        """

        def threader(func: Callable, *args, join: bool = False, **kwargs) -> None:
            """threads a function.

            Args:
                func (Callable): Function to thread.
                *args: Arguments for func.
                join (bool, optional): Whether to join thread. Defaults to True.
                **kwargs: Keyword arguments for func.
            """

            job_thread = Thread(target=func, args=args, kwargs=kwargs)
            job_thread.start()
            if join:
                job_thread.join()

        logging.info("Starting scheduler")
        self.every(2).minutes.do(threader, self.import_realtime, Alert, join=True)
        self.every(12).seconds.do(threader, self.import_realtime, Vehicle, join=True)
        self.every(30).seconds.do(threader, self.import_realtime, Prediction, join=True)
        self.every().day.at("04:00", tz=timezone).do(threader, self.geojson_exports)
        self.every().day.at("03:30", tz=timezone).do(threader, self.nightly_import)
        while True:
            self.run_pending()
            time.sleep(1)

    def stop(self, full: bool = False) -> None:
        """Stops the scheduler.

        args:
            - `full (bool, optional)`: Whether to close db connection. Defaults to False.
        """
        self.clear()
        if full:
            self.close()
