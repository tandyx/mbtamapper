"""Feed Object for GTFS Loader"""
# pylint: disable=too-many-instance-attributes
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
import os
import time
import logging
import tempfile
from datetime import datetime
from dotenv import load_dotenv

import pandas as pd
from geojson import FeatureCollection, dump

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select, delete
from sqlalchemy import CursorResult
from helper_functions import get_date, to_sql, download_zip
from gtfs_schedule import *
from gtfs_realtime import *
from .query import Query
from .gtfs_base import GTFSBase

load_dotenv()


class Feed:
    """Loads GTFS data into a route_type specific SQLite database.
    This class also contains methods to query the database.

    Args:
        url (str): url of GTFS feed (default: MBTA GTFS feed)
        date (datetime): date to load (default: today)
    """

    temp_dir: str = tempfile.gettempdir()

    # pylint: disable=too-many-instance-attributes
    def __init__(self, url: str = None, date: datetime = None) -> None:
        self.url = url or os.environ.get("GTFS_ZIP_LINK")
        self.date = date or get_date()
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(Feed.temp_dir, self.gtfs_name)
        self.db_path = os.path.join(
            Feed.temp_dir, f"{self.gtfs_name}_{date.strftime('%Y%m%d')}.db"
        )
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = sessionmaker(self.engine, expire_on_commit=False)
        self.session = self.sessionmkr()

    def __repr__(self) -> str:
        return f"<Feed(url={self.url}, date={self.date.strftime('%Y%m%d')}))>"

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
            "calendar.txt": Calendar,
            "calendar_dates.txt": CalendarDate,
            "calendar_attributes.txt": CalendarAttribute,
            "stops.txt": Stop,
            "routes.txt": Route,
            "shapes.txt": ShapePoint,
            "trips.txt": Trip,
            "multi_route_trips.txt": MultiRouteTrip,
            "stop_times.txt": StopTime,
        }
        # ------------------------------- Dump Data ------------------------------- #
        for file, orm in table_dict.items():
            with pd.read_csv(
                os.path.join(self.zip_path, file), chunksize=chunksize, dtype=object
            ) as read:
                for chunk in read:
                    if file == "shapes.txt":
                        to_sql(self.session, chunk["shape_id"].drop_duplicates(), Shape)
                    to_sql(self.session, chunk, orm)

        logging.info("Loaded %s in %f s", self.gtfs_name, time.time() - start)

    def purge_and_filter(self) -> None:
        """Purges and filters the database."""

        query_obj = Query(os.environ.get("ALL_ROUTES").split(","))

        cal_stmt = delete(Calendar).where(
            Calendar.service_id.not_in(
                select(
                    query_obj.return_active_calendar_query(self.date).columns.service_id
                )
            )
        )

        for stmt in [cal_stmt]:
            res: CursorResult = self.session.execute(stmt)
            self.session.commit()  # seperate commits to avoid giant journal file
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)

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
                or not f"{self.gtfs_name}" in file
            ):
                continue
            os.remove(file_path)
            logging.info("Deleted file %s", file)

    def export_geojsons(self, key: str, file_path: str) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
        """

        query_obj = Query(os.environ.get(key).split(","))

        query_dict = {
            "stops": query_obj.return_parent_stops(),
            "shapes": query_obj.return_shapes_query(),
        }

        for name, query in query_dict.items():
            data = self.session.execute(query).all()
            if name == "stops":
                if "4" in query_obj.route_types:
                    data += self.session.execute(
                        select(Stop).where(Stop.vehicle_type == "4")
                    ).all()
                if key == "RAPID_TRANSIT":
                    data += self.session.execute(
                        Query(["3"]).return_parent_stops()
                    ).all()

                features = FeatureCollection([s[0].as_feature(self.date) for s in data])
            if name == "shapes":
                if key == "RAPID_TRANSIT":
                    data += self.session.execute(
                        select(Shape)
                        .join(Trip, Shape.shape_id == Trip.shape_id)
                        .join(Route, Trip.route_id == Route.route_id)
                        .where(
                            Route.line_id.in_(
                                ["line-SLWashington", "line-SLWaterfront"]
                            ),
                            Route.route_type != "2",
                        )
                    ).all()

                data = sorted(data, key=lambda x: x[0].shape_id, reverse=True)

                features = FeatureCollection([s[0].as_feature() for s in data])
            file_subpath = os.path.join(file_path, key, name + ".json")
            for path in [file_path, os.path.join(file_path, key)]:
                if not os.path.exists(path):
                    os.mkdir(path)

            with open(file_subpath, "w", encoding="utf-8") as file:
                dump(features, file)
                logging.info("Exported %s", file.name)
