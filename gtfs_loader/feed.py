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

import asteval
import geojson as gj
import pandas as pd
import requests as req
import sqlalchemy as sa
from sqlalchemy import event, exc
from sqlalchemy import orm as saorm

from gtfs_orms import *
from helper_functions import removes_session, timeit

from .query import Query


class Feed(Query):  # pylint: disable=too-many-instance-attributes
    """Loads GTFS data into a route_type specific SQLite database. \
        This class also contains methods to query the database. \
        inherits from Query class, which contains queries. \
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
    @event.listens_for(sa.Engine, "connect")
    def _on_connect(
        dbapi_connection: sqlite3.Connection,
        connection_record: sa.pool.ConnectionPoolEntry,
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
    @event.listens_for(sa.Engine, "close")
    def _on_close(
        dbapi_connection: sqlite3.Connection,
        connection_record: sa.pool.ConnectionPoolEntry,
    ) -> None:
        """Sets sqlite pragma on close automatically.

        Args:
            dbapi_connection (sqlite3.Connection): connection to sqlite database
            connection_record (ConnectionRecord, optional): connection record
        """
        if not isinstance(dbapi_connection, sqlite3.Connection):
            logging.warning("db %s is unsupported", dbapi_connection.__class__.__name__)
            return
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
            - `url (str)`: url of GTFS feed
        """
        super().__init__()
        self.url = url
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(tempfile.gettempdir(), self.gtfs_name)
        self.db_path = os.path.join(os.getcwd(), f"{self.gtfs_name}.db")
        self.engine = sa.create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = saorm.sessionmaker(self.engine, expire_on_commit=False)
        self.session = self.sessionmkr()
        self.scoped_session = saorm.scoped_session(self.sessionmkr)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.url}@{self.db_path})>"

    def __str__(self) -> str:
        return self.__repr__()

    @timeit
    def _download_gtfs(self, **kwargs) -> None:
        """Downloads the GTFS feed zip file into a temporary directory.

        args:
            - `**kwargs`: keyword arguments to pass to requests
        """
        source = req.get(self.url, timeout=10, **kwargs)
        if not source.ok:
            raise req.exceptions.HTTPError(f"download {self.url}: {source.status_code}")
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
            - `*args`: args to pass to pd.read_csv
            - `purge (bool)`: whether to purge the database before loading (default: True)
            - `**kwargs`: keyword args for pd.read_csv
        """
        # ------------------------------- Create Tables ------------------------------- #
        self._download_gtfs()
        if purge:
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)
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
            - `orm (Type[Alert | Vehicle | Prediction])`: realtime ORM type.
        """
        if orm not in __class__.__realtime_orms__:
            raise ValueError(f"{orm} is not a realtime ORM")
        session = self.scoped_session()
        dataset: list[LinkedDataset] = session.execute(
            self.get_dataset_query(orm.__realtime_name__)
        ).first()
        if not dataset:
            return
        self.to_sql(dataset[0].as_dataframe(), orm, purge=True)

    @timeit
    def purge_and_filter(self, date: datetime) -> None:
        """Purges and filters the database.

        Args:
            date (datetime): date to filter on
        """

        for stmt in (self.delete_calendars_query(date), self.delete_facilities_query()):
            res: sa.CursorResult = self.session.execute(stmt)
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)
        self.session.commit()

    @timeit
    def export_geojsons(self, key: str, *route_types: str, file_path: str) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `*route_types (str)`: route types to export
            - `file_path (str)`: path to export files to
        """
        #pylint:disable=unspecified-encoding
        query_obj = Query(*route_types)
        file_subpath = os.path.join(file_path, key)
        def_kwargs = {"mode": "w","encoding": "utf-8"}
        for path in (file_path, file_subpath):
            if not os.path.exists(path):
                os.mkdir(path)
        file: io.TextIOWrapper
        with open(os.path.join(file_subpath, "park.json"), **def_kwargs) as file:
            gj.dump(self.get_parking_features(key, query_obj), file)
            logging.info("Exported %s", file.name)
        with open(os.path.join(file_subpath, "shapes.json"), **def_kwargs) as file:
            gj.dump(self.get_shape_features(key, query_obj, "agency"), file)
            logging.info("Exported %s", file.name)
        with open(os.path.join(file_subpath, "parking.json"), **def_kwargs) as file:
            gj.dump(self.get_parking_features(key, query_obj), file)
            logging.info("Exported %s", file.name)
        with open(os.path.join(file_subpath, "stops.json"), **def_kwargs) as file:
            gj.dump(self.get_stop_features(key, query_obj, "child_stops", "routes"), file)
            logging.info("Exported %s", file.name)

    @removes_session
    def get_stop_features(self, key: str, query_obj: Query, *include: str) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `query_obj (Query)`: Query object
            - `*include (str)`: other orms to include\n
        returns:
            - `FeatureCollection`: stops as FeatureCollection
        """
        session = self.scoped_session()
        stops_data: list[tuple[Stop]]
        stops_data = session.execute(query_obj.parent_stops_query).all()
        if key == "RAPID_TRANSIT":
            stops_data += session.execute(Query("3").parent_stops_query).all()
        if "4" in query_obj.route_types:
            stops_data += session.execute(
                self.select(Stop).where(Stop.vehicle_type == "4")
            ).all()
        return gj.FeatureCollection([s[0].as_feature(*include) for s in stops_data])

    @removes_session
    def get_shape_features(
        self, key: str, query_obj: Query, *include: str
    ) -> gj.FeatureCollection:
        """Generates geojsons for shapes.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `query_obj (Query)`: Query object
            - `*include (str)`: other orms to include\n
        returns:
            - `FeatureCollection`: shapes as FeatureCollection
        """
        session = self.scoped_session()

        shape_data: list[tuple[Shape]] = session.execute(
            query_obj.get_shapes_query()
        ).all()

        if key == "RAPID_TRANSIT":
            shape_data += session.execute(
                self.get_shapes_from_route_query(*self.SL_ROUTES).where(
                    Route.route_type != "2"
                )
            ).all()

        return gj.FeatureCollection(
            [s[0].as_feature(*include) for s in sorted(shape_data, reverse=True)]
        )

    @removes_session
    def get_parking_features(
        self, key: str, query_obj: Query, *include: str
    ) -> gj.FeatureCollection:
        """Generates geojsons for facilities.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `query_obj (Query)`: Query object
            - `*include (str)`: other orms to include \n
        returns:
            - `FeatureCollection`: facilities as FeatureCollection
        """

        session = self.scoped_session()
        facilities: list[tuple[Facility]]
        facilities = session.execute(
            query_obj.get_facilities_query("parking-area")
        ).all()
        if key == "RAPID_TRANSIT":
            facilities += session.execute(
                Query("3").get_facilities_query("parking-area")
            ).all()
        if "4" in query_obj.route_types:
            facilities += session.execute(self.ferry_parking_query).all()
        return gj.FeatureCollection([f[0].as_feature(*include) for f in facilities])

    @removes_session
    def get_vehicles_feature(
        self, key: str, query_obj: Query, *include: str
    ) -> gj.FeatureCollection:
        """Returns vehicles as FeatureCollection.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `query_obj (Query)`: Query object
            - `*include (str)`: other orms to include \n
        Returns:
            - `FeatureCollection`: vehicles as FeatureCollection
        """
        session = self.scoped_session()
        if key == "RAPID_TRANSIT":
            vehicles_query = query_obj.get_vehicles_query(*self.SL_ROUTES)
        else:
            vehicles_query = query_obj.get_vehicles_query()
        if key in ("BUS", "ALL_ROUTES"):
            vehicles_query = vehicles_query.limit(150)
        data: list[tuple[Vehicle]] = []
        for attempt in range(10):
            try:
                data = session.execute(vehicles_query).all()
            except (exc.OperationalError, exc.DatabaseError) as error:
                logging.error("Failed to get vehicle data: %s", error)
            if any(v[0].predictions for v in data):
                break
            time.sleep(0.5)
        if not data:
            logging.error("No data returned in %s attemps", attempt + 1)
        return gj.FeatureCollection([v[0].as_feature(*include) for v in data])

    @removes_session
    def to_sql(
        self, data: pd.DataFrame, orm: Type[Base], purge: bool = False, **kwargs
    ) -> int:
        """Helper function to dump dataframe to sql.

        Args:
            - `data (pd.DataFrame)`: dataframe to dump
            - `orm (any)`: table to dump to
            - `purge (bool, optional)`: whether to purge table before dumping. Defaults to False.
            - `**kwargs`: keyword args to pass to pd.to_sql \n
        returns:
            - `int`: number of rows added
        """
        session = self.scoped_session()
        if purge:
            while True:
                try:
                    session.execute(self.delete(orm))
                    session.commit()
                    break
                except exc.IllegalStateChangeError:
                    time.sleep(1)

        try:
            res = data.to_sql(
                name=orm.__tablename__,
                con=self.engine,
                if_exists="append",
                index=False,
                **kwargs,
            )
        except exc.IntegrityError:
            res = self.to_sql(data.iloc[1:], orm, **kwargs)
        logging.info("Added %s rows to %s", res, orm.__tablename__)
        return res

    @removes_session
    def get_orm_json(
        self, _orm: type[Base], *include, geojson: bool = False, **params
    ) -> list[dict[str]] | gj.FeatureCollection:
        """Returns a dictionary of the ORM names and their corresponding JSON names.

        args:
            - `_orm (str)`: ORM to return.
            - `*include (str)`: other orms to include
            - `geojson (bool)`: use `geojson` rather than `json`\n
            - `**params`: keyword arguments to pass to the query\n
        Returns:
            - `list[dict[str]]`: dictionary of the ORM names and their corresponding JSON names.
        """
        session = self.scoped_session()
        # pylint: disable=eval-used
        cols = _orm.__table__.columns.keys()
        comp_ops = ["<", ">", "!"]
        # non_cols, param_list = []
        param_list = []
        non_cols = []
        for key, value in params.items():
            if value in {"null", "None", "none"}:
                p_item = {"key": key, "action": "IS", "value": "NULL"}
            else:
                op_index = next((key.find(op) for op in comp_ops if key.find(op) > 0), None)
                if op_index is None:
                    p_item = {"key": key, "action": "=", "value": value}
                elif not value and not key[op_index] == "!":
                    p_item = {
                            "key": key[:op_index],
                            "action": key[op_index],
                            "value": key[op_index + 1 :]
                        }
                else:
                    p_item = {"key": key[:op_index], "action": f"{key[op_index]}=", "value": value}
            if p_item["key"] in cols:
                param_list.append(p_item)
            else:
                non_cols.append(p_item)
        stmt = self.select(_orm).where(
                *(
                    sa.text(f"{_orm.__tablename__}.{v['key']} {v['action']} '{v['value']}'")
                    for v in param_list
                )
            )
        if non_cols:
            data = []
            _eval = asteval.Interpreter()
            for d in session.execute(stmt).all():
                for c in non_cols:
                    if not hasattr(d[0], c["key"]):
                        continue
                    if _eval(f"{getattr(d[0], c["key"])} {c["action"]} {c['value']}"):
                        data.append(d)
        else:
            data: list[tuple[Base]] = session.execute(stmt).all()
        if geojson:
            return gj.FeatureCollection([d[0].as_feature(*include) for d in data])
        return [d[0].as_json(*include) for d in data]

        # data: list[tuple[Base]] = session.execute(
        #     self.select(_orm).where(
        #         *(
        #             (
        #                 getattr(_orm, k) == None
        #                 if v in {"null", "None", "none"}
        #                 else (
        #                     text(
        #                         f"{_orm.__tablename__}.{k.split(k[next(k.find(op) for op in compare_ops if k.find(op) > 0)])[0]}"
        #                         + f"{k[next(k.find(op) for op in compare_ops if k.find(op) > 0)]}"
        #                         + f"{k.split(k[next(k.find(op) for op in compare_ops if k.find(op) > 0)])[-1]}"
        #                     )
        #                     if not v and any(op in k for op in compare_ops)
        #                     else (
        #                         text(
        #                             f"{_orm.__tablename__}.{k.replace(k[next(k.find(op) for op in compare_ops_eq if k.find(op) > 0)], "")}"
        #                             + f"{k[next(k.find(op) for op in compare_ops_eq if k.find(op) > 0)]}={v}"
        #                         )
        #                         if v and any(op in k for op in compare_ops_eq)
        #                         else getattr(_orm, k) == v
        #                     )
        #                 )
        #             )
        #             for k, v in params.items()
        #         )
        #     )
        # ).all()
