"""Feed Object for GTFS Loader"""

# pylint: disable=unused-wildcard-import, wildcard-import, unused-argument, too-many-instance-attributes, line-too-long, too-many-locals, too-many-branches

import io
import logging
import os
import shutil
import sqlite3
import tempfile
import textwrap
import time
import typing as t
from datetime import datetime
from zipfile import ZipFile

import asteval
import geojson as gj
import pandas as pd
import pandas.core.generic as pdcg
import requests as req
import sqlalchemy as sa
import timeout_function_decorator
from sqlalchemy import event, exc
from sqlalchemy import orm as saorm

from ..gtfs_orms import *
from ..helper_functions import removes_session, timeit
from .query import Query


class Feed:
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
        # TripProperty,
        MultiRouteTrip,
        StopTime,
        LinkedDataset,
        Facility,
        FacilityProperty,
        Transfer,
    )

    REALTIME_ORMS = (Alert, Vehicle, Prediction)

    PARKING_FILE = "parking.json"
    STOPS_FILE = "stops.json"
    SHAPES_FILE = "shapes.json"

    @staticmethod
    def find_orm(name: str) -> t.Type[Base] | None:
        """returns the `type` of the orm by name

        args:
            - `name (str)`: name of the orm
        returns:
            - `type[Base]`: type of the orm
        """
        for cls in Base.__subclasses__():
            if cls.__name__.lower() == name.lower():
                return cls
        return None

    @staticmethod
    @event.listens_for(sa.Engine, "connect")
    def _on_connect(
        dbapi_connection: sqlite3.Connection,
        connection_record: sa.pool.ConnectionPoolEntry,
    ) -> None:
        """Sets sqlite pragma for each connection,\
            automitcally called when a connection is created.

        Args:
            - `dbapi_connection (sqlite3.Connection)`: connection to sqlite database
            - `connection_record (ConnectionRecord, optional)`: connection record
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
            - `dbapi_connection (sqlite3.Connection)`: connection to sqlite database
            - `connection_record (ConnectionRecord, optional)`: connection record
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

    def _get_session(self, readonly: bool = False, **kwargs) -> saorm.Session:
        """returns a `Session` from `Feed.scoped_session`.

        wrapper for `sa.scoped_session.__call__(...)`

        args:
            - `readonly (bool)`: whether the session is readonly
            - `**kwargs`: keyword arguments to pass to `scoped_session` \n
        returns:
            - `Session`: session object
        """

        session = self.scoped_session(**kwargs)
        if not readonly:
            return session
        session.flush = lambda *a, **kw: logging.warning("flush on readonly session")
        return session

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
        self.scoped_session = saorm.scoped_session(
            saorm.sessionmaker(self.engine, expire_on_commit=False, autoflush=False)
        )

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
        try:
            source = req.get(self.url, timeout=10, **kwargs)
        except req.exceptions.SSLError:
            source = req.get(self.url, timeout=10, verify=False, **kwargs)
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
                chunk: pd.DataFrame
                for chunk in read:
                    if orm.__filename__ == "shapes.txt":
                        self.to_sql(chunk["shape_id"].drop_duplicates(), Shape)
                    if hasattr(orm, "index"):  # what if this is chunked? it explodes.
                        chunk["index"] = chunk.index
                    self.to_sql(chunk, orm)
        self.remove_zip()
        logging.info("Loaded %s", self.gtfs_name)

    @timeit
    @removes_session
    def import_realtime(self, orm: RealtimeOrms | str, use_cache: bool = True) -> None:
        """Imports realtime data into the database.

        Args:
            - `orm (RealtimeOrms | str)`: realtime ORM.
        """

        if isinstance(orm, str):
            orm = __class__.find_orm(orm)
        if orm not in __class__.REALTIME_ORMS:
            raise ValueError(f"{orm} is not a realtime ORM")

        dataset: LinkedDataset
        if use_cache and (_tmp := LinkedDataset.cache.get(orm.__realtime_name__)):
            dataset = LinkedDataset.from_dict(_tmp)
            logging.info("Using cached LinkedDataset for %s", orm.__realtime_name__)
        else:
            session = self._get_session(readonly=True)
            dataset = session.execute(
                Query.get_dataset_query(orm.__realtime_name__)
            ).one_or_none()[0]

        if use_cache:
            dataset.cache_key(key=orm.__realtime_name__)

        if not dataset:
            return
        self.to_sql(dataset.as_dataframe(), orm, purge=True)

    @timeit
    @removes_session
    def purge_and_filter(self, date: datetime) -> None:
        """Purges and filters the database.

        Args:
            - `date (datetime)`: date to filter on
        """
        session = self._get_session()
        for stmt in [
            Query.delete_calendars_query(date),
            Query.delete_facilities_query("parking-area", "bike-storage"),
        ]:
            res: sa.CursorResult = session.execute(stmt)
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)
        session.commit()

    @timeit
    def export_geojsons(self, key: str, *route_types: str, file_path: str) -> None:
        """exports static geojson files for routes, facilities and shapes

        args:
            - key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - *route_types (str): route types to export
            - file_path (str): path to export files to
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
        session = self._get_session(readonly=True)
        stops: list[tuple[Stop]] = session.execute(query_obj.parent_stops_query).all()
        if key == "rapid_transit":
            stops += session.execute(Query("3").parent_stops_query).all()
        if "4" in query_obj.route_types:
            stops += session.execute(
                query_obj.select(Stop).where(Stop.vehicle_type == "4")
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
        session = self._get_session(readonly=True)
        shapes: list[tuple[Shape]] = session.execute(query_obj.get_shapes_query()).all()
        if key in ["rapid_transit", "all_routes"]:
            shapes += session.execute(
                query_obj.get_shapes_from_route_query(*self.SL_ROUTES).where(
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

        session = self._get_session(readonly=True)
        facils: list[tuple[Facility]] = session.execute(
            query_obj.get_facilities_query("parking-area")
        ).all()
        if key == "rapid_transit":
            facils += session.execute(
                Query("3").get_facilities_query("parking-area")
            ).all()
        if "4" in query_obj.route_types:
            facils += session.execute(query_obj.ferry_parking_query).all()
        return gj.FeatureCollection([f[0].as_feature(*include) for f in facils])

    @removes_session
    def get_vehicles_feature(
        self,
        key: str,
        query_obj: Query,
        *include: str,
        attempts: int = 10,
        timeout: int = 0.5,
    ) -> gj.FeatureCollection:
        """Returns vehicles as FeatureCollection.
        notes:
            - early return if ferry data is requested.
            - tries 10 times to get data \n
        args:
            - `key (str)`: the type of data to export (RAPID_TRANSIT, BUS, etc.)
            - `query_obj (Query)`: Query object
            - `*include (str)`: other orms to include
            - `attemps (int)`: num attempts default: 10
            - `timeout (float)`: timeout to take between attempts default 0.5 seconds \n
        returns:
            - `FeatureCollection`: vehicles as FeatureCollection
        """
        session = self._get_session(readonly=True)
        if key == "ferry":  # no ferry data :(
            return gj.FeatureCollection([])
        _routes: list[str] = []
        if key == "rapid_transit":
            _routes.extend(self.SL_ROUTES)
            # _routes.extend([*self.SL_ROUTES, "Shuttle-Generic"])
        data: list[tuple[Vehicle]] = []
        for _ in range(attempts):
            try:
                data = session.execute(query_obj.get_vehicles_query(*_routes)).all()
            except (exc.OperationalError, exc.DatabaseError) as error:
                logging.error("Failed to get vehicle data: %s", error)
            if any(v[0].predictions for v in data):
                break
            time.sleep(timeout)
        if not data:
            logging.error("No pred data returned in %s attemps", attempts)
        return gj.FeatureCollection([v[0].as_feature(*include) for v in data])

    @removes_session
    def to_sql(
        self, data: pdcg.NDFrame, orm: t.Type[Base], purge: bool = False, **kwargs
    ) -> int | None:
        """Helper function to dump dataframe to sql.

        Args:
            - `data (pd.DataFrame)`: dataframe to dump
            - `orm (any)`: table to dump to
            - `purge (bool, optional)`: whether to purge table before dumping. Defaults to False.
            - `**kwargs`: keyword args to pass to pd.to_sql \n
        returns:
            - `int`: number of rows added
        """
        session = self._get_session()
        if purge:
            while True:
                try:
                    session.execute(Query.delete(orm))
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

    def _get_orms(self, _orm: type[Base] | str, **params) -> list[tuple[Base]]:
        """
        basically executes a query

        args:
            - `_orm (str)`: ORM to return.
            - `**params`: keyword arguments to pass to the query\n
        returns:
            - `list[tuple[Base]]`: list of tuples of the ORM objects
        """
        # pylint: disable=line-too-long

        session = self._get_session(readonly=True)
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
        stmt = Query.select(_orm).where(
            *(
                sa.text(
                    f"""{_orm.__tablename__}.{v['key']} {v['action']} {v['value'] if v['value'] == 'NULL' else f'\'{v["value"]}\''}"""
                )
                for v in param_list
            )
        )
        data: list[tuple[Base]] = []
        if non_cols:
            _eval = asteval.Interpreter()
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
            data = session.execute(stmt).all()

        return data

    @removes_session
    def get_orms(self, _orm: type[Base] | str, **params) -> list[tuple[Base]]:
        """
        basically executes a query

        this removes the session, so it's suitable for public calls (wrapper for _get_orms)

        this is mostly for debugging

        args:
            - `_orm (str)`: ORM to return.
            - `**params`: keyword arguments to pass to the query\n
        returns:
            - `list[tuple[Base]]`: list of tuples of the ORM objects
        """

        return self._get_orms(_orm, **params)

    @removes_session
    def get_orm_json(
        self, _orm: type[Base] | str, *include: str, geojson: bool = False, **params
    ) -> list[dict[str, t.Any]] | gj.FeatureCollection:
        """Returns a dictionary of the ORM names and their corresponding JSON names.

        args:
            - `_orm (str)`: ORM to return.
            - `*include (str)`: other orms to include
            - `geojson (bool)`: use `geojson` rather than `json`\n
            - `**params`: keyword arguments to pass to the query\n
        returns:
            - `list[dict[str]]`: dictionary of the ORM names and their corresponding JSON names.
        """
        data = self._get_orms(_orm, **params)
        if geojson:
            if not data:
                return gj.FeatureCollection([])
            if callable(getattr(data[0][0], "as_feature", None)):
                return gj.FeatureCollection([d[0].as_feature(*include) for d in data])
            raise ValueError(f"{_orm} does not have an as_feature method")
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
