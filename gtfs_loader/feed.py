"""Feed Object for GTFS Loader"""

# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# pylint: disable=unused-argument
# pylint: disable=too-many-instance-attributes
# pylint: disable=line-too-long
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
import io
import logging
import os
import shutil
import sqlite3
import tempfile
import textwrap
import time
from datetime import datetime
from typing import Type
from zipfile import ZipFile

import asteval
import geojson as gj
import pandas as pd
import requests as req
import sqlalchemy as sa
import timeout_function_decorator
from sqlalchemy import event, exc
from sqlalchemy import orm as saorm

from gtfs_orms import *
from helper_functions import removes_session, timeit

from .query import Query


class Feed(Query):
    """Loads GTFS data into a route_type specific SQLite database. \
        This class also contains methods to query the database. \
        inherits from Query class, which contains queries. \
    This class is thread-safe.
        

    Args:
        - `url (str)`: url of GTFS feed
        - `gtfs_name (str, optional)`: name of GTFS feed. Defaults to auto-parsed from url.
    """

    SL_ROUTES = ("741", "742", "743", "751", "749", "746")

    # note that the order of these tables matters; avoids foreign key errors
    SCHEDULE_ORMS = (
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

    REALTIME_ORMS = (Alert, Vehicle, Prediction)

    PARKING_FILE = "parking.json"
    STOPS_FILE = "stops.json"
    SHAPES_FILE = "shapes.json"

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

    def __init__(self, url: str, gtfs_name: str | None = None) -> None:
        """
        Initializes Feed object with url.

        Parses url to get GTFS name and create db path in temp dir.

        Args:
            - `url (str)`: url of GTFS feed
            - `gtfs_name (str, optional)`: name of GTFS feed. Defaults to auto-parsed from url.
        """
        super().__init__()
        self.url = url
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = gtfs_name or url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(tempfile.gettempdir(), self.gtfs_name)
        self.db_path = os.path.join(os.getcwd(), f"{self.gtfs_name}.db")
        self.engine = sa.create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = saorm.sessionmaker(self.engine, expire_on_commit=False)
        self.scoped_session = saorm.scoped_session(self.sessionmkr)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.url}@{self.gtfs_name}.db)>"

    def __str__(self) -> str:
        return self.__repr__()

    @timeit
    def download_gtfs(self, **kwargs) -> None:
        """Downloads the GTFS feed zip file into a temporary directory.

        args:
            - `**kwargs`: keyword arguments to pass to `requests.get()`
        """
        source = req.get(self.url, timeout=10, **kwargs)
        if not source.ok:
            raise req.exceptions.HTTPError(f"download {self.url}: {source.status_code}")
        with ZipFile(io.BytesIO(source.content)) as zipfile_bytes:
            zipfile_bytes.extractall(self.zip_path)
        logging.info("Downloaded zip from %s to %s", self.url, self.zip_path)

    def remove_zip(self) -> None:
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
        self.download_gtfs()
        if purge:
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)
        # ------------------------------- Dump Data ------------------------------- #
        for orm in __class__.SCHEDULE_ORMS:
            with pd.read_csv(
                os.path.join(self.zip_path, orm.__filename__), *args, **kwargs
            ) as read:
                for chunk in read:
                    if orm.__filename__ == "shapes.txt":
                        self.to_sql(chunk["shape_id"].drop_duplicates(), Shape)
                    self.to_sql(chunk, orm)
        self.remove_zip()
        logging.info("Loaded %s", self.gtfs_name)

    @timeit
    @removes_session
    def import_realtime(self, orm: Type[Alert | Vehicle | Prediction] | str) -> None:
        """Imports realtime data into the database.

        Args:
            - `orm (Type[Alert | Vehicle | Prediction] | str)`: realtime ORM.
        """
        session = self.scoped_session()
        if isinstance(orm, str):
            orm = __class__.find_orm(orm)
        if orm not in __class__.REALTIME_ORMS:
            raise ValueError(f"{orm} is not a realtime ORM")
        dataset: list[LinkedDataset] = session.execute(
            self.get_dataset_query(orm.__realtime_name__)
        ).first()
        if not dataset:
            return
        self.to_sql(dataset[0].as_dataframe(), orm, purge=True)

    @timeit
    @removes_session
    def purge_and_filter(self, date: datetime) -> None:
        """Purges and filters the database.

        Args:
            - `date (datetime)`: date to filter on
        """
        session = self.scoped_session()
        for stmt in [self.delete_calendars_query(date), self.delete_facilities_query()]:
            res: sa.CursorResult = session.execute(stmt)
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)
        session.commit()

    @timeit
    def export_geojsons(self, key: str, *route_types: str, file_path: str) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `*route_types (str)`: route types to export
            - `file_path (str)`: path to export files to
        """
        # pylint:disable=unspecified-encoding
        query_obj = Query(*route_types)
        file_subpath = os.path.join(file_path, key)
        def_kwargs = {"mode": "w", "encoding": "utf-8"}
        for path in (file_path, file_subpath):
            if not os.path.exists(path):
                os.mkdir(path)
        file: io.TextIOWrapper
        with open(os.path.join(file_subpath, self.SHAPES_FILE), **def_kwargs) as file:
            gj.dump(self.get_shape_features(key, query_obj, "agency"), file)
            logging.info("Exported %s", file.name)
        with open(os.path.join(file_subpath, self.PARKING_FILE), **def_kwargs) as file:
            gj.dump(self.get_parking_features(key, query_obj), file)
            logging.info("Exported %s", file.name)
        with open(os.path.join(file_subpath, self.STOPS_FILE), **def_kwargs) as file:
            gj.dump(
                self.get_stop_features(key, query_obj, "child_stops", "routes"), file
            )
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
        stops: list[tuple[Stop]] = session.execute(query_obj.parent_stops_query).all()
        if key == "rapid_transit":
            stops += session.execute(Query("3").parent_stops_query).all()
        if "4" in query_obj.route_types:
            stops += session.execute(
                self.select(Stop).where(Stop.vehicle_type == "4")
            ).all()
        return gj.FeatureCollection([s[0].as_feature(*include) for s in stops])

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
        shapes: list[tuple[Shape]] = session.execute(query_obj.get_shapes_query()).all()
        if key in ["rapid_transit", "all_routes"]:
            shapes += session.execute(
                self.get_shapes_from_route_query(*self.SL_ROUTES).where(
                    Route.route_type != "2"
                )
            ).all()
        return gj.FeatureCollection(
            [s[0].as_feature(*include) for s in sorted(set(shapes), reverse=True)]
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
        facils: list[tuple[Facility]] = session.execute(
            query_obj.get_facilities_query("parking-area")
        ).all()
        if key == "rapid_transit":
            facils += session.execute(
                Query("3").get_facilities_query("parking-area")
            ).all()
        if "4" in query_obj.route_types:
            facils += session.execute(self.ferry_parking_query).all()
        return gj.FeatureCollection([f[0].as_feature(*include) for f in facils])

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
        if key == "rapid_transit":
            vehicles_query = query_obj.get_vehicles_query(*self.SL_ROUTES)
        else:
            vehicles_query = query_obj.get_vehicles_query()
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
        self, _orm: type[Base] | str, *include: str, geojson: bool = False, **params
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
        # pylint: disable=line-too-long
        session = self.scoped_session()
        if isinstance(_orm, str):
            _orm = self.find_orm(_orm)
        if not _orm:
            return []
        comp_ops = ["<", ">", "!"]
        param_list: list[dict[str, str]] = []
        non_cols: list[dict[str, str]] = []
        for key, value in params.items():
            if value in {"null", "None", "none"}:
                if "!" in key:
                    p_item = {
                        "key": key.replace("!", ""),
                        "action": "IS NOT",
                        "value": "NULL",
                    }
                else:
                    p_item = {"key": key, "action": "IS", "value": "NULL"}
            else:
                op_index = next(
                    (key.find(op) for op in comp_ops if key.find(op) > 0), None
                )
                if op_index is None:
                    p_item = {"key": key, "action": "=", "value": value}
                elif not value and not key[op_index] == "!":
                    p_item = {
                        "key": key[:op_index],
                        "action": key[op_index],
                        "value": key[op_index + 1 :],
                    }
                else:
                    p_item = {
                        "key": key[:op_index],
                        "action": f"{key[op_index]}=",
                        "value": value,
                    }
            if p_item["key"] in _orm.cols:
                param_list.append(p_item)
            else:
                non_cols.append(p_item)
        stmt = self.select(_orm).where(
            *(
                sa.text(
                    f"""{_orm.__tablename__}.{v['key']} {v['action']} {v['value'] if v['value'] == 'NULL' else f'\'{v["value"]}\''}"""
                )
                for v in param_list
            )
        )
        if non_cols:
            _eval = asteval.Interpreter()
            data = []
            for d in session.execute(stmt).all():
                for c in non_cols:
                    if hasattr(d[0], c["key"]):
                        if _eval.eval(
                            textwrap.dedent(
                                f"""
                                "{getattr(d[0], c['key'])}" {c['action'].lower() if c['action'] != '=' else '=='} "{c['value'].replace('NULL', 'None')}"
                            """
                            ).replace("\n", "")
                        ):
                            data.append(d)
        else:
            data: list[tuple[Base]] = session.execute(stmt).all()
        if geojson:
            return gj.FeatureCollection([d[0].as_feature(*include) for d in data])
        return [d[0].as_json(*include) for d in data]

    def timeout_get_orm_json(
        self,
        _orm: type[Base] | str,
        *include: str,
        timeout=15,
        geojson: bool = False,
        **params,
    ) -> list[dict[str]] | gj.FeatureCollection:
        """timeout version of `Feed.get_orm_json`;\
            to not specify a timeout, use that function
            
        args:
            - `_orm (str)`: ORM to return.
            - `*include (str)`: other orms to include
            - `timeout (int)`: timeout for the function in seconds
            - `geojson (bool)`: use `geojson` rather than `json`\n
            - `**params`: keyword arguments to pass to the query\n
        Returns:
            - `list[dict[str]]`: dictionary of the ORM names and their corresponding JSON names.
        """

        @timeout_function_decorator.timeout(timeout)
        def _get_orm_json():
            return self.get_orm_json(_orm, *include, geojson=geojson, **params)

        return _get_orm_json()

    def close(self) -> None:
        """Closes the connection to the database."""
        self.engine.dispose()
