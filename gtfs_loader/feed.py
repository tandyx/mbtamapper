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
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select

from shared_code.download_zip import download_zip
from shared_code.to_sql import to_sql
from shared_code.return_date import get_date
from gtfs_schedule import *
from gtfs_realtime import *
from .query import Query
from .gtfs_base import GTFSBase


class Feed:
    """Loads GTFS data into a route_type specific SQLite database.
    This class also contains methods to query the database.

    Args:
        url (str): url of GTFS feed
        date (datetime): date to load (default: today)
    """

    temp_dir: str = tempfile.gettempdir()

    # pylint: disable=too-many-instance-attributes
    def __init__(self, url: str, date: datetime = None) -> None:
        self.url = url
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
                        to_sql(self.engine, chunk["shape_id"].drop_duplicates(), Shape)
                    to_sql(self.engine, chunk, orm)

        logging.info("Loaded %s in %f s", self.gtfs_name, time.time() - start)

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

    def export_geojsons(self, query_obj: Query, file_path="") -> None:
        """Generates geojsons for stops and shapes.

        Args:
            query (Query): Query object
            file_path (str): path to save geojsons to (default: current directory)
        """
        query_dict = {
            "stops": query_obj.return_parent_stops(),
            "shapes": query_obj.return_shapes_query(),
        }

        def open_helper(data, file_name):
            """Helper function to open files."""
            path_to = os.path.join(file_path, file_name)
            with open(path_to, "w", encoding="utf-8") as file:
                dump(data, file)
                logging.info("Exported %s", file.name)

        for name, query in query_dict.items():
            data = self.session.execute(query).all()

            if name == "stops":
                if "4" in query_obj.route_types:
                    data += self.session.execute(
                        select(Stop).where(Stop.vehicle_type == "4")
                    ).all()
                if "0" in query_obj.route_types or "1" in query_obj.route_types:
                    data += self.session.execute(
                        Query(["3"]).return_parent_stops()
                    ).all()

            if name == "shapes" and (
                "0" in query_obj.route_types or "1" in query_obj.route_types
            ):
                data += self.session.execute(
                    select(Shape)
                    .join(Trip, Shape.shape_id == Trip.shape_id)
                    .join(Route, Trip.route_id == Route.route_id)
                    .where(
                        Route.line_id.in_(["line-SLWashington", "line-SLWaterfront"])
                    )
                ).all()
            features = FeatureCollection([s[0].as_feature() for s in data])

            if query_obj.route_types == ["0", "1", "2", "3", "4"]:
                open_helper(features, f"{name}_all.json")
            else:
                for route_type in query_obj.route_types:
                    open_helper(features, f"{name}_{route_type}.json")
