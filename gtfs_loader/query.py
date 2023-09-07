"""Defines a class to hold and generate queries."""
# pylint: disable=unused-wildcard-import
# pylint: disable=unused-import
# pylint: disable=wildcard-import
from datetime import datetime, timedelta
from sqlalchemy.sql import select, selectable, or_, and_, not_
from sqlalchemy.orm import aliased
from gtfs_schedule import *
from gtfs_realtime import Vehicle


class Query:
    """Class to hold and generate queries.

    Args:
        route_types (list[str]): list of route_types to query
    """

    def __init__(self, route_types: list[str] = None) -> None:
        self.route_types = route_types or []
        self.trip_query = self.return_trip_query()
        self.parent_stops_query = self.return_parent_stops()

    def __repr__(self) -> str:
        return f"<Query(route_types={self.route_types})>"

    def return_active_calendar_query(self, date: datetime) -> selectable.Select:
        """Returns a query for active calendars on a date.

        Args:
            date (datetime): date to query"""

        return (
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
                        Calendar.start_date
                        <= (date + timedelta(days=7)).strftime("%Y%m%d"),
                        Calendar.end_date >= date.strftime("%Y%m%d"),
                        getattr(Calendar, date.strftime("%A").lower()) == 1,
                        not_(
                            and_(
                                CalendarDate.date == date.strftime("%Y%m%d"),
                                CalendarDate.exception_type == "2",
                                CalendarDate.service_id.isnot(None),
                            )
                        ),
                    ),
                    and_(
                        CalendarDate.date == date.strftime("%Y%m%d"),
                        CalendarDate.exception_type == "1",
                        CalendarDate.service_id.isnot(None),
                        CalendarAttribute.service_schedule_typicality != "6",
                    ),
                )
            )
        )

    def return_trip_query(self) -> selectable.Select:
        """Returns a query for trips."""
        return (
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

    def return_parent_stops(self) -> selectable.Select:
        """Returns a query for parent stops.

        Returns:
            A query for parent stops.
        """

        parent = aliased(Stop)
        return (
            select(parent)
            .distinct()
            .where(parent.location_type == "1")
            .join(Stop, parent.stop_id == Stop.parent_station)
            .join(StopTime, Stop.stop_id == StopTime.stop_id)
            .where(StopTime.trip_id.in_(select(self.trip_query.columns.trip_id)))
        )

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

    def return_vehicles_query(self, add_routes: str) -> selectable.Select:
        """Returns a query for vehicles.

        Args:
            add_routes (str): comma-separated string of route_ids to add to the query
        """

        return (
            select(Vehicle)
            .distinct()
            .join(Route, Vehicle.route_id == Route.route_id)
            .where(
                or_(
                    Vehicle.route_id.in_(
                        select(self.return_routes_query().columns.route_id)
                    ),
                    Vehicle.trip_id.in_(select(self.trip_query.columns.trip_id)),
                    Vehicle.route_id.in_(add_routes.split(",")),
                )
            )
        )

    def return_facilities_query(self, types: list[str] = None) -> selectable.Select:
        """Returns a query for parking facilities.

        Args:
            types (list[str]): list of facility types, default: ["parking-area", "bike-storage"]
        """
        return (
            select(Facility)
            .distinct()
            .where(
                Facility.stop_id.in_(select(self.parent_stops_query.columns.stop_id)),
                Facility.facility_type.in_(types or ["parking-area", "bike-storage"]),
            )
        )
