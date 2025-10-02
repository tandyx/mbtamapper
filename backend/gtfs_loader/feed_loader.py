"""FeedLoader class."""

import logging
import os
import typing as t

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler

from ..gtfs_orms import Alert, LinkedDataset, Prediction, Shape, Vehicle
from ..helper_functions import TimeZones, get_date, timeit
from .feed import Feed


class FeedLoader(Feed):
    """Loads GTFS data into map \
        and schedules jobs to import realtime data.

    Args:
        url (str): URL of GTFS feed
        geojson_path (str): Path to save geojsons
        keys_dict (dict[str, list[str]]): Dictionary of keys to load
        kwargs: Keyword arguments to pass to `Feed`, such as `gtfs_name`
    """

    @property
    def geojsons_exist(self) -> bool:
        """if *all* geojsons exist"""
        return all(
            os.path.exists(os.path.join(self.geojson_path, k, fname))
            for k in self.keys_dict
            for fname in [self.SHAPES_FILE, self.PARKING_FILE, self.STOPS_FILE]
        )

    @property
    def db_exists(self) -> bool:
        """if the database exists"""
        return os.path.exists(self.db_path)

    def __init__(
        self,
        url: str,
        geojson_path: str,
        keys_dict: dict[str, list[str]],
        timezone: TimeZones = "America/New_York",
        **kwargs,
    ) -> None:
        """Initializes FeedLoader.

        Args:
            url (str): URL of GTFS feed.
            geojson_path (str): Path to save geojsons.
            keys_dict (dict[str, list[str]]): Dictionary of keys to load.
            timezone (str, optional): Timezone. Defaults to "America/New_York".
            kwargs: passed to both BackgroundScheduler
        """

        super().__init__(url)

        self.url = url
        self.keys_dict = keys_dict
        self.geojson_path = geojson_path

        self.scheduler = BackgroundScheduler(timezone=timezone, **kwargs)

    @timeit
    def nightly_import(self, **kwargs) -> None:
        """Runs the nightly import.

        args:
            kwargs: keyword arguments to pass to `import_gtfs`.\n
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

    def import_and_run(self, import_data: bool = False, **kwargs) -> t.NoReturn:
        """this is the main entrypoint for the application.

        Args:
            import_data (bool, optional): reloads the database and geojsons.\
                Defaults to False.
            timezone (str, optional): Timezone. Defaults to "America/New_York".
            kwargs: Keyword arguments to pass to `nightly import`.
        """

        if import_data or not self.db_exists:
            self.nightly_import(**kwargs)
        if import_data or not self.geojsons_exist:
            self.geojson_exports()
        self.run()

    def clear_caches(self) -> None:
        """clears orm-specific caches"""
        Shape.cache.clear()
        LinkedDataset.cache.clear()
        logging.warning("caches cleared")

    def run(self, force: bool = False) -> t.Self:
        """Schedules jobs defined by FeedLoader

        Args:
            force (bool, optional): forces this through if running. Defaults to False.

        Returns:
            t.Self: this class
        """
        if self.scheduler.running:
            logging.warning("calling scheduler while already running!")
            if not force:
                logging.warning("not adding jobs!")
                return self

        self.scheduler.add_job(
            self.import_realtime, "interval", args=[Alert], minutes=1
        )
        self.scheduler.add_job(
            self.import_realtime, "interval", args=[Vehicle], seconds=11
        )
        self.scheduler.add_job(
            self.import_realtime, "interval", args=[Prediction], seconds=21
        )
        self.scheduler.add_job(self.geojson_exports, "cron", hour=4, minute=0)
        self.scheduler.add_job(self.nightly_import, "cron", hour=3, minute=30)
        self.scheduler.add_job(self.clear_caches, "cron", day="*/4", hour=3, minute=40)
        self.scheduler.start()
        jobs: list[Job] = self.scheduler.get_jobs()

        logging.info(
            "FeedLoader scheduler started\n%s",
            "\n".join(f"{j.name}: next run @ {j.next_run_time}" for j in jobs),
        )
        return self

    def stop(self, full: bool = False) -> None:
        """Stops the scheduler.

        Args:
            full (bool, optional): Whether to close db connection. Defaults to False.
        """
        self.scheduler.shutdown(wait=False)
        if full:
            self.close()
