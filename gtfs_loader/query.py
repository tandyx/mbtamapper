"""Defines a class to hold and generate queries."""
# pylint: disable=unused-wildcard-import
# pylint: disable=unused-import
# pylint: disable=wildcard-import
from datetime import datetime
from sqlalchemy.sql import select, selectable, or_, not_, and_
from sqlalchemy.orm import aliased
from gtfs_schedule import *


class Query:
    """Class to hold and generate queries.

    Args:
        route_types (list[str]): list of route_types to query
    """

    def __init__(self, route_types: list[str] = None) -> None:
        self.route_types = route_types or []
        self.trip_query = self.return_trip_query()

    def __repr__(self) -> str:
        return f"<Query(route_types={self.route_types})>"

    def return_active_calendar_query(self, date: datetime) -> selectable.Select:
        """Returns a query for active calendars on a date.

        Args:
            date (datetime): date to query"""

        cal_query = (
            select(Calendar)
            .join(
                CalendarAttribute, Calendar.service_id == CalendarAttribute.service_id
            )
            .join(
                CalendarDate,
                Calendar.service_id == CalendarDate.service_id,
                isouter=True,
            )
            .where(
                or_(
                    and_(
                        CalendarAttribute.service_schedule_typicality != "6",
                        Calendar.start_date <= date.strftime("%Y%m%d"),
                        Calendar.end_date >= date.strftime("%Y%m%d"),
                        # getattr(Calendar, date.strftime("%A").lower()) == 1,
                        #     not_(
                        #         and_(
                        #             CalendarDate.date == date.strftime("%Y%m%d"),
                        #             CalendarDate.exception_type == "2",
                        #             CalendarDate.service_id.isnot(None),
                        #         )
                        #     ),
                        # ),
                        # and_(
                        #     CalendarDate.date == date.strftime("%Y%m%d"),
                        #     CalendarDate.exception_type == "1",
                        #     CalendarDate.service_id.isnot(None),
                        #     CalendarAttribute.service_schedule_typicality != "6",
                    ),
                )
            )
        )

        return cal_query

    def return_trip_query(self) -> selectable.Select:
        """Returns a query for trips."""
        trip_query = (
            select(Trip)
            .distinct()
            .join(Route, Trip.route_id == Route.route_id)
            .where(
                or_(
                    Route.route_type.in_(self.route_types),
                    Trip.trip_id.in_(
                        select(Trip.trip_id)
                        .distinct()
                        .join(MultiRouteTrip, Trip.trip_id == MultiRouteTrip.trip_id)
                        .join(Route, MultiRouteTrip.added_route_id == Route.route_id)
                        .where(Route.route_type.in_(self.route_types))
                    ),
                )
            )
        )

        return trip_query

    def return_parent_stops(self) -> selectable.Select:
        """Returns a query for parent stops.

        Returns:
            A query for parent stops.
        """

        parent = aliased(Stop)
        query = (
            select(parent)
            .distinct()
            .where(parent.location_type == "1")
            .join(Stop, parent.stop_id == Stop.parent_station)
            .join(StopTime, Stop.stop_id == StopTime.stop_id)
            .where(StopTime.trip_id.in_(select(self.trip_query.columns.trip_id)))
        )

        return query

    def return_shapes_query(self) -> selectable.Select:
        """Returns a query for shapes."""
        return (
            select(Shape)
            .distinct()
            .join(Trip, Shape.shape_id == Trip.shape_id)
            .where(Trip.trip_id.in_(select(self.trip_query.columns.trip_id)))
        )

    def return_routes_query(self) -> selectable.Select:
        """Returns a query for routes."""

        return (
            select(Route)
            .distinct()
            .where(Route.route_id.in_(select(self.trip_query.columns.route_id)))
        )
