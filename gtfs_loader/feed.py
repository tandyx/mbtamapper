"""Feed Object for GTFS Loader"""
# pylint: disable=too-many-instance-attributes
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
import os
import time
import logging
import tempfile
from datetime import datetime

import pandas as pd
from geojson import FeatureCollection, dump

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import CursorResult
from helper_functions import get_current_time, to_sql, download_zip

from gtfs import *
from .query import Query


class Feed:
    """Loads GTFS data into a route_type specific SQLite database.
    This class also contains methods to query the database.

    Args:
        url (str): url of GTFS feed
    """

    TEMP_DIR: str = tempfile.gettempdir()
    # note that the order of these tables matters; avoids foreign key errors
    INSERTION_TUPLE = (
        Agency,
        Calendar,
        CalendarDate,
        CalendarAttribute,
        Stop,
        Route,
        ShapePoint,
        Trip,
        MultiRouteTrip,
        StopTime,
        LinkedDataset,
        Facility,
        FacilityProperty,
    )

    # SILVER_LINE_ROUTES = "741,742,743,751,749,746"

    def __init__(self, url: str) -> None:
        """Initializes Feed object.

        Args:
            url (str): url of GTFS feed
        """
        self.url = url
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(__class__.TEMP_DIR, self.gtfs_name)
        self.db_path = os.path.join(__class__.TEMP_DIR, f"{self.gtfs_name}.db")
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = sessionmaker(self.engine, expire_on_commit=False)
        self.session = self.sessionmkr()
        self.scoped_session = scoped_session(self.sessionmkr)

    def __repr__(self) -> str:
        return f"<Feed(url={self.url})>"

    def import_gtfs(self, *args, purge: bool = True, **kwargs) -> None:
        """Dumps GTFS data into a SQLite database.

        Args:
            *args: args for import_gtfs
            purge (bool): whether to purge the database before loading (default: False)
            **kwargs: keyword args for import_gtfs
        """
        # ------------------------------- Create Tables ------------------------------- #
        start = time.time()
        download_zip(self.url, self.zip_path)
        if purge:
            GTFSBase.metadata.drop_all(self.engine)
            GTFSBase.metadata.create_all(self.engine)
        # ------------------------------- Dump Data ------------------------------- #
        for orm in __class__.INSERTION_TUPLE:
            with pd.read_csv(
                os.path.join(self.zip_path, orm.__filename__), *args, **kwargs
            ) as read:
                for chunk in read:
                    if orm.__filename__ == "shapes.txt":
                        to_sql(self.session, chunk["shape_id"].drop_duplicates(), Shape)
                    to_sql(self.session, chunk, orm)

        logging.info("Loaded %s in %f s", self.gtfs_name, time.time() - start)

    def import_realtime(self, orm: GTFSBase) -> None:
        """Imports realtime data into the database.

        Args:
            orm (GTFSBase): table to import into, must be Alert, Prediction, or Vehicle
        """
        session = self.scoped_session()
        dataset_mapper = {
            Alert: ["service_alerts", "process_service_alerts"],
            Prediction: ["trip_updates", "process_trip_updates"],
            Vehicle: ["vehicle_positions", "process_vehicle_positions"],
        }

        if orm not in dataset_mapper:
            logging.error("Invalid ORM: %s", orm)
            return

        dataset = session.execute(
            Query.select(LinkedDataset).where(
                getattr(LinkedDataset, dataset_mapper[orm][0])
            )
        ).all()

        to_sql(
            session, getattr(dataset[0][0], dataset_mapper[orm][1])(), orm, purge=True
        )
        self.scoped_session.remove()

    def purge_and_filter(self, date: datetime) -> None:
        """Purges and filters the database.

        Args:
            date (datetime): date to filter on
        """

        for stmt in (Query.delete_calendars(date), Query.delete_facilities()):
            res: CursorResult = self.session.execute(stmt)
            self.session.commit()  # seperate commits to avoid giant journal file
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)

    def export_geojsons(
        self, key: str, route_types: list[str], file_path: str, date: datetime = None
    ) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            route_types (list[str]): route types to export
            file_path (str): path to export files to
            date (datetime): date to export (default: today)
        """
        date = date or get_current_time()
        query_obj = Query(route_types)
        file_subpath = os.path.join(file_path, key)
        for path in (file_path, file_subpath):
            if not os.path.exists(path):
                os.mkdir(path)
        self.export_parking_lots(key, file_subpath, query_obj)
        self.export_shapes(key, file_subpath, query_obj)
        self.export_stops(key, file_subpath, query_obj, date)

    def export_stops(
        self, key: str, file_path: str, query_obj: Query, date: datetime
    ) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
            date (datetime): date to export
        """
        session = self.scoped_session()

        stops_data = session.execute(query_obj.parent_stops_query).all()
        if key == "RAPID_TRANSIT":
            stops_data += session.execute(Query(("3",)).parent_stops_query).all()
        if "4" in query_obj.route_types:
            stops_data += session.execute(
                Query.select(Stop).where(Stop.vehicle_type == "4")
            ).all()

        features = FeatureCollection([s[0].as_feature(date) for s in stops_data])
        with open(os.path.join(file_path, "stops.json"), "w", encoding="utf-8") as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

        self.scoped_session.remove()

    def export_shapes(self, key: str, file_path: str, query_obj: Query) -> None:
        """Generates geojsons for shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
        """
        session = self.scoped_session()

        shape_data = session.execute(query_obj.get_shapes()).all()

        if key == "RAPID_TRANSIT":
            shape_data += session.execute(
                Query.get_shapes_from_route(
                    ("line-SLWashington", "line-SLWaterfront")
                ).where(
                    Route.route_type != "2",
                )
            ).all()

        features = FeatureCollection(
            [
                s[0].as_feature()
                for s in sorted(shape_data, key=lambda x: x[0].shape_id, reverse=True)
            ]
        )
        with open(
            os.path.join(file_path, "shapes.json"), "w", encoding="utf-8"
        ) as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

        self.scoped_session.remove()

    def export_parking_lots(self, key: str, file_path: str, query_obj: Query) -> None:
        """Generates geojsons for facilities.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
        """

        session = self.scoped_session()

        facilities = session.execute(query_obj.get_facilities(["parking-area"])).all()

        if key == "RAPID_TRANSIT":
            facilities += session.execute(
                Query(["3"]).get_facilities(["parking-area"])
            ).all()

        if "4" in query_obj.route_types:
            facilities += session.execute(Query.get_ferry_parking()).all()
        features = FeatureCollection([f[0].as_feature() for f in facilities])
        with open(os.path.join(file_path, "park.json"), "w", encoding="utf-8") as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

        self.scoped_session.remove()

    # def export_vehicle_geojson(self, key: str, query_obj: Query, path: str) -> None:
    #     """Exports vehicle geojson.

    #     Args:
    #         key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
    #         query_obj (Query): Query object
    #         path (str): path to export files to
    #     """

    #     sess = self.scoped_session()
    #     add_routes = Feed.SILVER_LINE_ROUTES if key == "RAPID_TRANSIT" else ""
    #     vehicles_query = query_obj.get_vehicles(add_routes)
    #     # if key in ["BUS", "ALL_ROUTES"]:
    #     #     vehicles_query = vehicles_query.limit(75)
    #     data: list[tuple[Vehicle]]
    #     attempts = 0
    #     try:
    #         while attempts <= 10:
    #             data = sess.execute(vehicles_query).all()
    #             if data and any(d[0].predictions for d in data) or key == "FERRY":
    #                 break
    #             attempts += 1
    #             time.sleep(1)
    #     except OperationalError as error:
    #         data = []
    #         logging.error("Failed to send data: %s", error)
    #     if not data:
    #         logging.error("No data returned in %s attemps", attempts)
    #     feature_collection = FeatureCollection([v[0].as_feature() for v in data])

    #     with open(
    #         os.path.join(path, key, "vehicles.json"), "w", encoding="utf-8"
    #     ) as file:
    #         dump(feature_collection, file)
    #         logging.info("Exported %s", file.name)

    # def get_vehicles(self, query: Query, **kwargs) -> FeatureCollection:
    #     """Returns vehicles as FeatureCollection.

    #     Args:
    #         query (Query): Query object
    #         **kwargs: keyword arguments for Query object
    #     """
    #     session = self.scoped_session()
    #     data: list[tuple[Vehicle]]
    #     try:
    #         data = session.execute(query.get_vehicles(**kwargs)).all()
    #     except OperationalError:
    #         data = []
    #     self.scoped_session.remove()
    #     return FeatureCollection([v[0].as_feature() for v in data])
