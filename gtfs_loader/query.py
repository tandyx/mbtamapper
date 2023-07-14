"""Class to store query information for GTFS data."""

from sqlalchemy import or_, not_, and_
from sqlalchemy.sql import selectable, select

from gtfs_schedule import *  # pylint: disable=unused-wildcard-import


class Query:
    """Class to store query information for GTFS data.

    Args:
        route_type (str): Route type to query for.
    """

    def __init__(self, route_type: str):
        self.route_type = route_type
        self.mrt_query = self.return_mrt_query()
        self.base_stop_query = self.return_base_stop_query()
        self.parent_stops_query = self.return_parent_stops_query()
        self.platform_stops_query = self.return_platform_stops_query()
        self.route_trips = self.return_route_trips_query()

    def __repr__(self) -> str:
        return f"<Query(route_types={self.route_type})>"

    def return_mrt_query(self) -> selectable.Select:
        """Returns query for multi route trips"""
        mrt_subquery = (
            select(Trip)
            .join(Route, Trip.route_id == Route.route_id)
            .where(Route.route_type == self.route_type)
            .subquery()
        )

        mrt_query = (
            select(MultiRouteTrip)
            .join(Route, MultiRouteTrip.added_route_id == self.route_type)
            .outerjoin(
                mrt_subquery, MultiRouteTrip.trip_id == mrt_subquery.columns.trip_id
            )
            .where(
                Route.route_type == self.route_type,
                mrt_subquery.columns.trip_id.is_(None),
            )
        )

        return mrt_query

    def return_base_stop_query(self) -> selectable.Select:
        """Returns base stop query"""
        active_stops = (
            select(Stop, Trip)
            .join(StopTime, Stop.stop_id == StopTime.stop_id)
            .join(Trip, StopTime.trip_id == Trip.trip_id)
            .distinct()
        )

        return active_stops

    def return_parent_stops_query(self) -> selectable.Select:
        """Returns query for parent stations"""
        parent_stops = (
            select(Stop)
            .distinct()
            .where(
                Stop.stop_id.in_(select(self.base_stop_query.columns.parent_station))
            )
        )

        return parent_stops

    def return_platform_stops_query(self) -> selectable.Select:
        """Returns query for platform stops"""
        platform_stops = (
            select(Stop)
            .distinct()
            .where(
                and_(
                    Stop.parent_station.in_(
                        select(self.base_stop_query.columns.parent_station)
                    ),
                    Stop.vehicle_type == self.route_type,
                )
            )
        )

        return platform_stops

    def return_route_trips_query(self) -> selectable.Select:
        """Returns query for route trips"""
        route_trips = (
            select(Trip)
            .join(Route, Trip.route_id == Route.route_id)
            .where(
                or_(
                    Route.route_type == self.route_type,
                    Trip.trip_id.in_(select(self.mrt_query.columns.trip_id)),
                    Route.route_id.in_(select(self.mrt_query.columns.added_route_id)),
                )
            )
        )

        return route_trips
