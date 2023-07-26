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
    """

    temp_dir: str = tempfile.gettempdir()

    def __init__(self, url: str) -> None:
        self.url = url
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(Feed.temp_dir, self.gtfs_name)
        self.db_path = os.path.join(Feed.temp_dir, f"{self.gtfs_name}.db")
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.sessionmkr = sessionmaker(self.engine, expire_on_commit=False)
        self.session = self.sessionmkr()

    def __repr__(self) -> str:
        return f"<Feed(url={self.url})>"

    def import_gtfs(self, chunksize: int = 10**5, purge: bool = True) -> None:
        """Dumps GTFS data into a SQLite database.

        Args:
            chunksize (int): number of rows to insert at a time (default: 10**5),
            purge (bool): whether to purge the database before loading (default: False)
        """
        # ------------------------------- Create Tables ------------------------------- #
        start = time.time()
        download_zip(self.url, self.zip_path)
        if purge:
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
            "linked_datasets.txt": LinkedDataset,
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

    def import_realtime(self) -> None:
        """Imports realtime data into the database."""

        dataset_mapper = {
            Alert: "process_service_alerts",
            Prediction: "process_trip_updates",
            Vehicle: "process_vehicle_positions",
        }

        dataset: tuple[LinkedDataset]
        for dataset in self.session.execute(select(LinkedDataset)).all():
            for orm, func in dataset_mapper.items():
                if not dataset[0].is_dataset(orm):
                    continue
                try:
                    to_sql(self.session, getattr(dataset[0], func)(), orm, True)
                    break
                except KeyError:
                    logging.error(
                        "Error processing %s for %s", orm.__tablename__, dataset[0].url
                    )

    def purge_and_filter(self, date: datetime = None) -> None:
        """Purges and filters the database.

        Args:
            date (datetime): date to filter on, defaults to today"""
        date = date or get_date()
        query_obj = Query(os.environ.get("ALL_ROUTES").split(","))

        cal_stmt = delete(Calendar).where(
            Calendar.service_id.not_in(
                select(query_obj.return_active_calendar_query(date).columns.service_id)
            )
        )

        for stmt in [cal_stmt]:
            res: CursorResult = self.session.execute(stmt)
            self.session.commit()  # seperate commits to avoid giant journal file
            logging.info("Deleted %s rows from %s", res.rowcount, stmt.table.name)

    def export_geojsons(self, key: str, file_path: str, date: datetime = None) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            date (datetime): date to export (default: today)
        """

        query_obj = Query(os.environ.get(key).split(","))
        file_subpath = os.path.join(file_path, key)
        for path in [file_path, file_subpath]:
            if not os.path.exists(path):
                os.mkdir(path)

        self.export_shapes(key, file_subpath, query_obj)
        self.export_stops(key, file_subpath, query_obj, date)

    def export_stops(
        self, key: str, file_path: str, query_obj: Query, date: datetime = None
    ) -> None:
        """Generates geojsons for stops and shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
            date (datetime): date to export (default: today)
        """

        stops_data = self.session.execute(query_obj.return_parent_stops()).all()
        if key == "RAPID_TRANSIT":
            stops_data += self.session.execute(Query(["3"]).return_parent_stops()).all()
        if "4" in query_obj.route_types:
            stops_data += self.session.execute(
                select(Stop).where(Stop.vehicle_type == "4")
            ).all()

        with open(os.path.join(file_path, "stops.json"), "w", encoding="utf-8") as file:
            dump(
                FeatureCollection(
                    [s[0].as_feature(date or get_date()) for s in stops_data]
                ),
                file,
            )
            logging.info("Exported %s", file.name)

    def export_shapes(self, key: str, file_path: str, query_obj: Query) -> None:
        """Generates geojsons for shapes.

        Args:
            key (str): the type of data to export (RAPID_TRANSIT, BUS, etc.)
            file_path (str): path to export files to
            query_obj (Query): Query object
        """

        shape_data = self.session.execute(query_obj.return_shapes_query()).all()

        if key == "RAPID_TRANSIT":
            shape_data += self.session.execute(
                select(Shape)
                .join(Trip, Shape.shape_id == Trip.shape_id)
                .join(Route, Trip.route_id == Route.route_id)
                .where(
                    Route.line_id.in_(["line-SLWashington", "line-SLWaterfront"]),
                    Route.route_type != "2",
                )
            ).all()

            shape_data = sorted(shape_data, key=lambda x: x[0].shape_id, reverse=True)

        with open(
            os.path.join(file_path, "shapes.json"), "w", encoding="utf-8"
        ) as file:
            dump(
                FeatureCollection(
                    [
                        s[0].as_feature()
                        for s in sorted(
                            shape_data, key=lambda x: x[0].shape_id, reverse=True
                        )
                    ]
                ),
                file,
            )

            logging.info("Exported %s", file.name)
