"""Feed Object for GTFS Loader"""
import os
import time
import logging
import tempfile
from datetime import datetime

import pandas as pd

from sqlalchemy import create_engine, or_, not_, delete, CursorResult
from sqlalchemy.sql import select, insert, selectable
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import IntegrityError

from shared_code.download_zip import download_zip
from shared_code.to_sql import to_sql
from gtfs_schedule import *  # pylint: disable=unused-wildcard-import
from gtfs_realtime import *  # pylint: disable=unused-wildcard-import
from .gtfs_base import GTFSBase
from .query import Query
from poll_mbta_data import predictions, vehicles, alerts


class Feed:
    """Loads GTFS data into a route_type specific SQLite database.
    This class also contains methods to query the database.

    Args:
        url (str): url of GTFS feed
        route_types (str): route type to load
        date (datetime): date to load
        engine (bool): whether to create an engine and session (default: True)
    """

    temp_dir: str = tempfile.gettempdir()

    # pylint: disable=too-many-instance-attributes
    def __init__(self, url: str, route_type: str, date: datetime) -> None:
        self.url = url
        self.route_type = route_type
        self.date = date
        self.queries = Query(route_type)
        # ------------------------------- Connection/Session Setup ------------------------------- #
        self.gtfs_name = url.rsplit("/", maxsplit=1)[-1].split(".")[0]
        self.zip_path = os.path.join(Feed.temp_dir, self.gtfs_name)
        self.db_path = os.path.join(
            Feed.temp_dir, f"{self.gtfs_name}_{route_type}_{date.strftime('%Y%m%d')}.db"
        )
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.session = sessionmaker(self.engine, expire_on_commit=False)()

    def __repr__(self) -> str:
        return f"<Feed(url={self.url}, route_type={self.route_type})>"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Feed):
            return NotImplemented
        return self.url == __value.url and self.route_type == __value.route_type

    def __hash__(self) -> int:
        return hash((self.url, self.route_type))

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

    def return_query(self, query: selectable.Select) -> list[tuple[GTFSBase]]:
        """Returns a list of tuples of the specified table."""
        with self.session.begin():
            return self.session.execute(query).all()

    def query_vehicles(self, use_session: Session = None) -> list[tuple[Vehicle]]:
        """Downloads realtime data from the mbta api and returns active vehicles.
        Note that this method also deletes all realtime data from the database and replaces it

        Args:
            use_session (Session): optional session to use (default: this feed's session)
        Returns:
            list[tuple[Vehicle]]: list of vehicles"""

        use_session = use_session or self.session
        # GTFSBase.metadata.drop_all(
        #     self.engine,
        #     tables=[Vehicle.__table__, Alert.__table__, Prediction.__table__],
        # )

        # GTFSBase.metadata.create_all(
        #     self.engine,
        #     tables=[Vehicle.__table__, Alert.__table__, Prediction.__table__],
        # )

        orm_func_mapper = {
            Vehicle: vehicles.get_vehicles,
            Alert: alerts.get_alerts,
            Prediction: predictions.get_predictions,
        }

        active_routes = ",".join(
            item[0]
            for item in self.session.execute(select(Route.route_id).distinct()).all()
        )
        vehicle_list = []
        for orm, function in orm_func_mapper.items():
            data = function(self.route_type if orm != Prediction else active_routes)
            try:
                self.session.execute(delete(orm))
                self.session.execute(
                    insert(orm), data.to_dict(orient="records", index=True)
                )
            except IntegrityError:
                logging.error("Error inserting %s", orm.__name__)
            self.session.commit()
        vehicle_list += self.session.execute(select(Vehicle)).all()

        return vehicle_list
