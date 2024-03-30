"""Feed Object for GTFS Loader"""

# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# pylint: disable=unused-argument
import io
import logging
import os
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime
from typing import Type
from zipfile import ZipFile

import pandas as pd
import requests as req
from geojson import FeatureCollection, dump
from sqlalchemy import CursorResult, Engine, create_engine, event, exc, pool
from sqlalchemy.exc import IllegalStateChangeError, IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker

from gtfs_orms import *
from helper_functions import get_current_time, removes_session, timeit

from .query import Query


class Feed(Query):  # pylint: disable=too-many-instance-attributes
    """Loads GTFS data into a route_type specific SQLite database. \
        This class also contains methods to query the database. \
        inherits from Query class, which contains queries. \
    \n
    This class is thread-safe.
        

    Args:
        url (str): url of GTFS feed
    """

    SL_ROUTES = ("741", "742", "743", "751", "749", "746")

    # note that the order of these tables matters; avoids foreign key errors
    __schedule_orms__ = (
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

    __realtime_orms__ = (Alert, Vehicle, Prediction)

    @staticmethod
    @event.listens_for(Engine, "connect")
    def _on_connect(
        dbapi_connection: sqlite3.Connection,
        connection_record: pool.ConnectionPoolEntry,
    ) -> None:
        """Sets sqlite pragma for each connection,\
            automitcally called when a connection is created.

        Args:
            dbapi_connection (sqlite3.Connection): connection to sqlite database
            connection_record (ConnectionRecord, optional): connection record
        """

        if not isinstance(dbapi_connection, sqlite3.Connection):
            logging.warning("db %s is unsupported", dbapi_connection.__class__.__name__)
            return

        cursor = dbapi_connection.cursor()
        for pragma in ["foreign_keys=ON", "auto_vacuum='1'", "shrink_memory"]:
            try:
                cursor.execute(f"PRAGMA {pragma}")
            except sqlite3.OperationalError:
                logging.warning("PRAGMA %s failed", pragma)
        cursor.close()

    @staticmethod
    @event.listens_for(Engine, "close")
    def _on_close(
        dbapi_connection: sqlite3.Connection,
        connection_record: pool.ConnectionPoolEntry,
    ) -> None:
        """Sets sqlite pragma on close automatically.

        Args:
            dbapi_connection (sqlite3.Connection): connection to sqlite database
            connection_record (ConnectionRecord, optional): connection record
        """
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA optimize")
            except sqlite3.OperationalError:
                logging.warning("PRAGMA optimize failed")
            cursor.close()

    def __init__(self, url: str) -> None:
        """
        Initializes Feed object with url.

        Parses url to get GTFS name and create db path in temp dir.

        Args:
            url (str): url of GTFS feed
        """
        super().__init__()
        self.url = url
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(tempfile.gettempdir(), self.gtfs_name)
        self.db_path = os.path.join(tempfile.gettempdir(), f"{self.gtfs_name}.db")
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = sessionmaker(self.engine, expire_on_commit=False)
        self.session = self.sessionmkr()
        self.scoped_session = scoped_session(self.sessionmkr)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(url={self.url})>"

    def __str__(self) -> str:
        return self.__repr__()

    @timeit
    def _download_gtfs(self) -> None:
        """Downloads the GTFS feed zip file into a temporary directory."""
        source = req.get(self.url, timeout=10)
        if not source.ok:
            raise req.exceptions.HTTPError(
                f"couldn't download {self.url}: {source.status_code}"
            )
        with ZipFile(io.BytesIO(source.content)) as zipfile_bytes:
            zipfile_bytes.extractall(self.zip_path)
        logging.info("Downloaded zip from %s to %s", self.url, self.zip_path)

    def _remove_zip(self) -> None:
        """Removes the GTFS zip file."""
        if not os.path.exists(self.zip_path):
            logging.warning("%s does not exist", self.zip_path)
            return
        shutil.rmtree(self.zip_path)
        logging.info("Removed %s", self.zip_path)

    @timeit
    def import_gtfs(self, *args, purge: bool = True, **kwargs) -> None:
        """Dumps GTFS data into a SQLite database.

        Args:
            *args: args to pass to pd.read_csv
            purge (bool): whether to purge the database before loading (default: False)
            **kwargs: keyword args for pd.read_csv
        """
        # ------------------------------- Create Tables ------------------------------- #
        self._download_gtfs()
        if purge:
            GTFSBase.metadata.drop_all(self.engine)
            GTFSBase.metadata.create_all(self.engine)
        # ------------------------------- Dump Data ------------------------------- #
        for orm in __class__.__schedule_orms__:
            with pd.read_csv(
                os.path.join(self.zip_path, orm.__filename__), *args, **kwargs
            ) as read:
                for chunk in read:
                    if orm.__filename__ == "shapes.txt":
                        self.to_sql(chunk["shape_id"].drop_duplicates(), Shape)
                    self.to_sql(chunk, orm)
        self._remove_zip()
        logging.info("Loaded %s", self.gtfs_name)

    @timeit
    @removes_session
    def import_realtime(self, orm: Type[Alert | Vehicle | Prediction]) -> None:
        """Imports realtime data into the database.

        Args:
            orm (Type[Alert | Vehicle | Prediction]): realtime ORM type.
        """
        if orm not in __class__.__realtime_orms__:
            raise ValueError(f"{orm} is not a realtime ORM")
        session = self.scoped_session()

        dataset: list[LinkedDataset] = session.execute(
            self.get_dataset_query(orm.__realtime_name__)
        ).first()

        self.to_sql(dataset[0].as_dataframe(), orm, purge=True)

    @timeit
    def purge_and_filter(self, date: datetime) -> None:
        """Purges and filters the database.

        Args:
            date (datetime): date to filter on
        """

        for stmt in (self.delete_calendars_query(date), self.delete_facilities_query()):
            res: CursorResult = self.session.execute(stmt)
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)
        self.session.commit()

    @timeit
    def export_geojsons(
        self, key: str, route_types: tuple[str], file_path: str, date: datetime = None
    ) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            route_types (list[str]): route types to export
            file_path (str): path to export files to
            date (datetime): date to export (default: today)
        """
        date = date or get_current_time()
        query_obj = Query(*route_types)
        file_subpath = os.path.join(file_path, key)
        for path in (file_path, file_subpath):
            if not os.path.exists(path):
                os.mkdir(path)
        self.export_parking_lots(key, file_subpath, query_obj)
        self.export_shapes(key, file_subpath, query_obj)
        self.export_stops(key, file_subpath, query_obj, date)

    @removes_session
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
            stops_data += session.execute(Query("3").parent_stops_query).all()
        if "4" in query_obj.route_types:
            stops_data += session.execute(
                self.select(Stop).where(Stop.vehicle_type == "4")
            ).all()

        features = FeatureCollection([s[0].as_feature(date) for s in stops_data])
        with open(os.path.join(file_path, "stops.json"), "w", encoding="utf-8") as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

    @removes_session
    def export_shapes(self, key: str, file_path: str, query_obj: Query) -> None:
        """Generates geojsons for shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
        """
        session = self.scoped_session()

        shape_data: list[tuple[Shape]] = session.execute(
            query_obj.get_shapes_query()
        ).all()

        if key == "RAPID_TRANSIT":
            shape_data += session.execute(
                self.get_shapes_from_route_query(self.SL_ROUTES).where(
                    Route.route_type != "2"
                )
            ).all()

        features = FeatureCollection(
            [s[0].as_feature() for s in sorted(shape_data, reverse=True)]
        )
        with open(
            os.path.join(file_path, "shapes.json"), "w", encoding="utf-8"
        ) as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

    @removes_session
    def export_parking_lots(self, key: str, file_path: str, query_obj: Query) -> None:
        """Generates geojsons for facilities.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
        """

        session = self.scoped_session()

        facilities = session.execute(
            query_obj.get_facilities_query(["parking-area"])
        ).all()
        if key == "RAPID_TRANSIT":
            facilities += session.execute(
                Query("3").get_facilities_query(["parking-area"])
            ).all()
        if "4" in query_obj.route_types:
            facilities += session.execute(self.ferry_parking_query).all()
        features = FeatureCollection([f[0].as_feature() for f in facilities])
        with open(os.path.join(file_path, "park.json"), "w", encoding="utf-8") as file:
            dump(features, file)
            logging.info("Exported %s", file.name)

    @removes_session
    def get_vehicles_feature(
        self, key: str, *route_types: str, max_tries: int = 10
    ) -> FeatureCollection:
        """Returns vehicles as FeatureCollection.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            *route_types (str): route types to export
            max_tries (int): maximum number of tries to get data (default: 5)
        Returns:
            FeatureCollection: vehicles as FeatureCollection
        """
        session = self.scoped_session()
        vehicles_query = Query(*route_types).get_vehicles_query(
            self.SL_ROUTES if key == "RAPID_TRANSIT" else []
        )
        if key in ("BUS", "ALL_ROUTES"):
            vehicles_query = vehicles_query.limit(75)
        data: list[tuple[Vehicle]] = []
        for attempt in range(max_tries):
            try:
                data = session.execute(vehicles_query).all()
            except (exc.OperationalError, exc.DatabaseError) as error:
                logging.error("Failed to get vehicle data: %s", error)
            if any(v[0].predictions for v in data):
                break
            time.sleep(0.5)
        if not data:
            logging.error("No data returned in %s attemps", attempt + 1)
        return FeatureCollection([v[0].as_feature() for v in data])

    @removes_session
    def to_sql(
        self, data: pd.DataFrame, orm: Type[GTFSBase], purge: bool = False, **kwargs
    ) -> int:
        """Helper function to dump dataframe to sql.

        Args:
            data (pd.DataFrame): dataframe to dump
            orm (any): table to dump to
            purge (bool, optional): whether to purge table before dumping. Defaults to False.
            **kwargs: keyword args to pass to pd.to_sql
        """

        session = self.scoped_session()

        if purge:
            while True:
                try:
                    session.execute(self.delete(orm))
                    session.commit()
                    break
                except IllegalStateChangeError:
                    time.sleep(1)

        try:
            res = data.to_sql(
                name=orm.__tablename__,
                con=self.engine,
                if_exists="append",
                index=False,
                **kwargs,
            )
        except IntegrityError:
            res = self.to_sql(data.iloc[1:], orm, **kwargs)
        logging.info("Added %s rows to %s", res, orm.__tablename__)
        return res
