"""FeedLoader class."""

import logging
import os
import typing as t

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from geojson import FeatureCollection

from ..gtfs_orms import Alert, LinkedDataset, Prediction, Shape, Vehicle
from ..helper_functions import PathLike, get_date, timeit
from .feed import Feed
from .query import Query

# pylint: disable=line-too-long


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
        log_file: PathLike = "mbtamapper.log",
        **kwargs,
    ) -> None:
        """Initializes FeedLoader.

        Args:
            url (str): URL of GTFS feed.
            geojson_path (str): Path to save geojsons.
            keys_dict (dict[str, list[str]]): Dictionary of keys to load\
               as {route_key: ["1", "2", ...]}
            url_base (str, optional): web app url base "http://localhost:5000".
            timezone (str, optional): Timezone. Defaults to "America/New_York".
            kwargs: passed to BackgroundScheduler
        """

        super().__init__(url)

        self.url: str = url
        self.keys_dict: dict[str, list[str]] = keys_dict
        self.geojson_path: str = geojson_path
        self.log_file: PathLike = log_file
        # self.url_base: str = url_base.rstrip("/")
        self.scheduler = BackgroundScheduler(
            timezone=kwargs.get("timezone", "America/New_York"), **kwargs
        )

        self.vehicle_cache: dict[str, FeatureCollection] = {}
        """in-memory cache of vehicles"""

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
        self.vehicle_cache.clear()
        logging.warning("caches cleared")

    def get_vehicles_feature_cache(
        self, key: str, *include: str, **kwargs
    ) -> FeatureCollection:
        """the same as the super method, but:

        abstracts `Query` away \n
        and loads the result into the self.vehicle_cache

        Args:
            key (str): route key to use
            *include (str): attrs to include
            **kwargs: dumped to super class

        Returns:
            FeatureCollection: vehicles as featurecollection
        """

        if (cache_key := f"{key}-{','.join(include)}") not in self.vehicle_cache:
            res = self.get_vehicles_feature(
                key, Query(*self.keys_dict[key]), *include, **kwargs
            )
            if res:
                self.vehicle_cache[cache_key] = res
        return self.vehicle_cache[cache_key]

    @timeit
    def _update_vehicle_cache(self, **kwargs) -> dict[str, FeatureCollection]:
        """updates cache and then returns the cache

        Returns:
            dict[str, FeatureCollection]: the cache
        """

        for cache_key in self.vehicle_cache:
            key, include = cache_key.split("-")
            self.vehicle_cache[cache_key] = self.get_vehicles_feature(
                key, Query(*self.keys_dict[key]), *include.split(","), **kwargs
            )

        while len(self.vehicle_cache) > 10:
            self.vehicle_cache.popitem()

        return self.vehicle_cache

    def clear_log(self, maxsize: int = 10**9) -> None:
        """_summary_

        Args:
            maxsize (int, optional): _description_. Defaults to 10**9 bytes (1 gb).
        """
        abs_path: PathLike = os.path.abspath(self.log_file)
        if not os.path.exists(self.log_file):
            logging.warning("file %s doesn't exist", abs_path)
        size: int = os.path.getsize(self.log_file)
        if os.path.exists(self.log_file) and size >= maxsize:
            os.remove(self.log_file)
            logging.info("removed file %s w/ size %s", abs_path, size)

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
        self.scheduler.add_job(self._update_vehicle_cache, "interval", seconds=10)

        self.scheduler.add_job(self.geojson_exports, "cron", hour=3, minute=45)
        self.scheduler.add_job(self.nightly_import, "cron", hour=3, minute=30)

        self.scheduler.add_job(self.clear_caches, "cron", day="*/4", hour=3, minute=40)
        self.scheduler.add_job(self.clear_log, "cron", hour=3, minute=45)

        self.scheduler.start()
        job: Job
        logging.info("FeedLoader scheduler started")
        for job in self.scheduler.get_jobs():
            logging.info("%s: next run @ %s", job.name, job.next_run_time or "never")
        return self

    def stop(self, full: bool = False) -> None:
        """Stops the scheduler.

        Args:
            full (bool, optional): Whether to close db connection. Defaults to False.
        """
        self.scheduler.shutdown(wait=False)
        if full:
            self.close()
