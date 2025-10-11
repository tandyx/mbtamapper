"""FeedLoader class."""

import logging
import os
import typing as t

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler

from ..gtfs_orms import Alert, LinkedDataset, Prediction, Shape, Vehicle
from ..helper_functions import get_date, timeit
from .feed import Feed

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
        url_base: str = "http://localhost:5000",
        **kwargs,
    ) -> None:
        """Initializes FeedLoader.

        Args:
            url (str): URL of GTFS feed.
            geojson_path (str): Path to save geojsons.
            keys_dict (dict[str, list[str]]): Dictionary of keys to load.
            url_base (str, optional): web app url base "http://localhost:5000".
            timezone (str, optional): Timezone. Defaults to "America/New_York".
            kwargs: passed to BackgroundScheduler
        """

        super().__init__(url)

        self.url: str = url
        self.keys_dict: dict[str, list[str]] = keys_dict
        self.geojson_path: str = geojson_path
        self.url_base: str = url_base.rstrip("/")
        self.scheduler = BackgroundScheduler(
            timezone=kwargs.get("timezone", "America/New_York"), **kwargs
        )

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

    # @timeit
    # def prime_caches(self) -> None:  # pylint: disable=too-many-locals,too-many-branches
    #     """primes caches for apis, etc."""
    #     today = get_date()
    #     stops_set: set[str] = set()
    #     routes_set: set[str] = set()

    #     for key, route_types in self.keys_dict.items():
    #         query_obj = Query(*route_types)
    #         vehicle_resp = req.get(f"{self.url_base}/{key}/vehicles", timeout=10)
    #         if vehicle_resp.ok:
    #             logging.info("primed %s vehicles cache", key)
    #         else:
    #             logging.error(
    #                 "error priming %s vehicles cache: %s", key, vehicle_resp.text
    #             )
    #         time.sleep(1)

    #     for key, route_types in {"commuter_rail": ["2"], "ferry": ["4"]}.items():
    #         query_obj = Query(*route_types)
    #         for stop in self.get_stop_features(key, query_obj, "child_stops")[
    #             "features"
    #         ]:
    #             if len(stop["properties"]["child_stops"]) < 4:
    #                 continue
    #             for child_stop in stop["properties"]["child_stops"]:
    #                 stop_id: str = child_stop["stop_id"]
    #                 if stop_id in stops_set or child_stop["location_type"] != "0":
    #                     logging.info("skipping stop %s", stop_id)
    #                     continue
    #                 cs_resp = req.get(
    #                     f"{self.url_base}/api/stoptime?stop_id={stop_id}&operates_today=True&_={today.strftime("%Y%m%d")}&include=trip&cache=86400",
    #                     timeout=10,
    #                 )
    #                 if cs_resp.ok:
    #                     logging.info("primed %s stoptimes cache", stop_id)
    #                     stops_set.add(stop_id)
    #                 else:
    #                     logging.error(
    #                         "error priming stop %s stoptimes cache: %s",
    #                         stop_id,
    #                         cs_resp.text,
    #                     )
    #                 time.sleep(1)

    #         for route in self.get_shape_features(key, query_obj)["features"]:
    #             route_id: str = route["properties"]["route_id"]
    #             if route_id in routes_set:
    #                 logging.info("skipping route %s", route_id)
    #                 continue
    #             route_resp = req.get(
    #                 f"{self.url_base}/api/route?route_id={route_id}&_={today.strftime('%Y%m%d')}&include=stop_times,trips&cache=86400",
    #                 timeout=10,
    #             )
    #             if route_resp.ok:
    #                 logging.info("primed shape %s cache", route_id)
    #                 routes_set.add(route_id)
    #             else:
    #                 logging.error(
    #                     "error priming shape %s cache: %s", route_id, route_resp.text
    #                 )
    #             time.sleep(1)

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
        self.scheduler.add_job(self.geojson_exports, "cron", hour=3, minute=45)
        self.scheduler.add_job(self.nightly_import, "cron", hour=3, minute=30)
        self.scheduler.add_job(self.clear_caches, "cron", day="*/4", hour=3, minute=40)
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
