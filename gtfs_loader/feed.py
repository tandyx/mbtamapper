"""Feed Object for GTFS Loader"""
import os
import time
import logging
import tempfile
from datetime import datetime

import pandas as pd

from sqlalchemy import create_engine, or_, not_, delete, CursorResult
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from shared_code.download_zip import download_zip
from shared_code.to_sql import to_sql
from gtfs_schedule import *  # pylint: disable=unused-wildcard-import
from gtfs_realtime import *  # pylint: disable=unused-wildcard-import
from .gtfs_base import GTFSBase
from .query import Query


class Feed:
    """Loads GTFS data into a route_type specific SQLite database.
    This class also contains methods to query the database.

    Args:
        url (str): url of GTFS feed
        route_types (str): route type to load
        date (datetime): date to load
    """

    temp_dir: str = tempfile.gettempdir()

    # pylint: disable=too-many-instance-attributes
    def __init__(self, url: str, route_type: str, date: datetime) -> None:
        self.url = url
        self.route_type = route_type
        self.date = date
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(Feed.temp_dir, self.gtfs_name)
        self.db_path = os.path.join(
            Feed.temp_dir, f"{self.gtfs_name}_{route_type}_{date.strftime('%Y%m%d')}.db"
        )
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.session = sessionmaker(self.engine)()
        # ------------------------------- Query Setup ------------------------------- #
        self.queries = Query(route_type)

    def __repr__(self) -> str:
        return f"<Feed(url={self.url}, route_type={self.route_type})>"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Feed):
            return NotImplemented
        return self.url == __value.url and self.route_type == __value.route_type

    def import_gtfs(self, chunksize: int = 10**5) -> None:
        """Dumps GTFS data into a SQLite database.

        Args:
            chunksize (int): number of rows to insert at a time (default: 10**5)
        """
        # ------------------------------- Create Tables ------------------------------- #
        start = time.time()
        download_zip(self.url, self.zip_path)
        GTFSBase.metadata.drop_all(self.engine)
        GTFSBase.metadata.create_all(self.engine)
        # note that the order of these tables matters; avoids foreign key errors
        table_dict = {
            "agency.txt": Agency,
            "stops.txt": Stop,
            "routes.txt": Route,
            "shapes.txt": ShapePoint,
            "trips.txt": Trip,
            "multi_route_trips.txt": MultiRouteTrip,
            "stop_times.txt": StopTime,
            "transfers.txt": Transfer,
        }
        # ------------------------------- Dump Data ------------------------------- #
        for file, orm in table_dict.items():
            with pd.read_csv(
                os.path.join(self.zip_path, file), chunksize=chunksize, dtype=object
            ) as read:
                for chunk in read:
                    if file == "shapes.txt":
                        shape_chunk = chunk["shape_id"].drop_duplicates()
                        try:
                            to_sql(self.engine, shape_chunk, Shape)
                        except IntegrityError:
                            to_sql(self.engine, shape_chunk.iloc[1:], Shape)
                    to_sql(self.engine, chunk, orm, file == "transfers.txt")

        logging.info("Loaded %s in %f s", self.gtfs_name, time.time() - start)

    def purge_and_filter(self) -> None:
        """Purges unused data from the database.

        This first deletes calendar dates that aren't active or associated with a trip
        with the specified route type or multi route trips. This cascades to trips and stoptimes. It
        then deletes stops, shapes, facilities, routes based off of the remaining trips/stoptimes.

        This is done to 1) save space and 2) make querying simplier (i.e. no need to filter)
        """

        start = time.time()

        trips_stmt = delete(Trip.__table__).where(
            Trip.trip_id.notin_(select(self.queries.route_trips.columns.trip_id))
        )

        stops_stmt = delete(Stop.__table__).where(
            not_(
                or_(
                    Stop.stop_id.in_(
                        select(self.queries.platform_stops_query.columns.stop_id)
                    ),
                    Stop.stop_id.in_(
                        select(self.queries.parent_stops_query.columns.stop_id),
                    ),
                )
            )
        )
        shapes_stmt = delete(Shape.__table__).where(
            Shape.shape_id.notin_(select(Trip.shape_id))
        )
        routes_stmt = delete(Route.__table__).where(
            Route.route_id.notin_(select(Trip.route_id).distinct()),
        )

        for stmt in [trips_stmt, stops_stmt, shapes_stmt, routes_stmt]:
            res: CursorResult = self.session.execute(stmt)
            self.session.commit()  # seperate commits to avoid giant journal file
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)

        logging.info(
            "Purged data from %s in %f seconds", self.db_path, time.time() - start
        )

    def delete_old_databases(self, days_ago: int = 2) -> None:
        """Deletes files older than 2 days from the given path and date.

        Args:
            days_ago (int): number of days ago to delete files from (default: 2)"""

        for file in os.listdir(Feed.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if (
                not file.endswith(".db")
                or not os.path.getmtime(file_path)
                < self.date.timestamp() - days_ago * 86400
                or not f"{self.gtfs_name}_{self.gtfs_name}" in file
            ):
                continue
            os.remove(file_path)
            logging.info("Deleted file %s", file)

    def close_connection(self) -> None:
        """Closes the connection to the database."""

        def close_conn_sub() -> None:
            self.session.close()
            self.engine.dispose()

        try:
            close_conn_sub()
        except:
            self.session.rollback()
            close_conn_sub()
