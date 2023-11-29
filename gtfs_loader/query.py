"""Defines a class to hold and generate queries."""
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
from datetime import datetime, timedelta

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import aliased
from sqlalchemy.sql import and_, delete, not_, or_, select, update
from sqlalchemy.sql.dml import Delete, Select, Update

from gtfs_orms import *


class Query:
    """Class to hold and generate queries.

    Args:
        route_types (list[str]): list of route_types to query
    """

    @staticmethod
    def select(*orms: DeclarativeMeta, **kwargs) -> Select[DeclarativeMeta]:
        """Returns a generic select query for tables.

        Args:
            *orms: tables to query
            **kwargs: kwargs for select
        Returns:
            A generic select query for tables.
        """
        return select(*orms, **kwargs)

    @staticmethod
    def delete(orm: DeclarativeMeta) -> Delete[DeclarativeMeta]:
        """Returns a generic delete query for a table.

        Args:
            orm (DeclarativeMeta): table to query
        Returns:
            A generic delete query for a table.
        """
        return delete(orm)

    @staticmethod
    def update(orm: DeclarativeMeta) -> Update[DeclarativeMeta]:
        """Returns a generic update query for a table.

        Args:
            orm (DeclarativeMeta): table to quer
        Returns:
            A generic update query for a table.
        """
        return update(orm)

    @staticmethod
    def get_active_calendars(
        date: datetime, specific: bool = False, days_ahead: int = 7
    ) -> Select:
        """Returns a query for active calendars on a date.

        Args:
            date (datetime): date to query
            specific (bool, optional): whether to query for specific date. \
                Defaults to False (query for week)
            days_ahead (int, optional): number of days ahead to query. Defaults to 7.
        Returns:
            A query for active calendars on a date.
        """
        if specific:
            return (
                select(Calendar)
                .join(
                    CalendarAttribute,
                    Calendar.service_id == CalendarAttribute.service_id,
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
                            getattr(Calendar, date.strftime("%A").lower()),
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
                        <= (date + timedelta(days=days_ahead)).strftime("%Y%m%d"),
                        Calendar.end_date >= date.strftime("%Y%m%d"),
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

    @staticmethod
    def delete_calendars(*args, **kwargs) -> Delete[DeclarativeMeta]:
        """Returns a query to delete calendars.

        Args:
            *args: args for get_active_calendars
            **kwargs: kwargs for get_active_calendars
        Returns:
            A query to delete calendars.
        """

        return delete(Calendar).where(
            Calendar.service_id.notin_(
                select(
                    __class__.get_active_calendars(*args, **kwargs).columns.service_id
                )
            )
        )

    @staticmethod
    def delete_facilities(exclude: list[str] = None) -> Delete[DeclarativeMeta]:
        """Returns a query to delete facilities.

        Args:
            exclude (list[str], optional): list of facility types to exclude.\
                Defaults to ["parking-area", "bike-storage"].
        Returns:
            A query to delete facilities.
        """

        return delete(Facility).where(
            Facility.facility_id.not_in(
                select(Facility.facility_id).where(
                    Facility.facility_type.in_(
                        exclude or ("parking-area", "bike-storage")
                    ),
                    Facility.stop_id.isnot(None),
                )
            )
        )

    @staticmethod
    def get_shapes_from_route(routes: list[str] = None) -> Select[DeclarativeMeta]:
        """Returns a query for shapes.

        Args:
            routes (list[str], optional): list of routes to query. Defaults to None.
        Returns:
            A query for shapes.
        """
        base_query = (
            select(Shape)
            .join(Trip, Shape.shape_id == Trip.shape_id)
            .join(Route, Trip.route_id == Route.route_id)
        )
        if not routes:
            return base_query
        return base_query.where(Route.route_id.in_(routes))

    @staticmethod
    def get_ferry_parking() -> Select[DeclarativeMeta]:
        """Returns a query for ferry parking."""
        return (
            select(Facility)
            .join(Stop, Facility.stop_id == Stop.stop_id)
            .where(Stop.vehicle_type == "4")
            .where(Facility.facility_type == "parking-area")
        )

    def __init__(self, route_types: list[str] = None) -> None:
        """Initializes Query.

        Args:
            route_types (list[str], optional): list of route_types to query. Defaults to None.
        """
        self.route_types = route_types or []
        self.trip_query = self.__get_trips()
        self.parent_stops_query = self.__get_parent_stops()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(route_types={self.route_types})>"

    def __str__(self) -> str:
        return self.__repr__()

    def __get_trips(self) -> Select[DeclarativeMeta]:
        """Returns a query for trips.

        Returns:
            A query for trips."""
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

    def __get_parent_stops(self) -> Select[DeclarativeMeta]:
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

    def get_shapes(self) -> Select[DeclarativeMeta]:
        """Returns a query for shapes.

        Returns:
            A query for shapes."""
        return (
            select(Shape)
            .distinct()
            .join(Trip, Shape.shape_id == Trip.shape_id)
            .where(Trip.trip_id.in_(select(self.trip_query.columns.trip_id)))
        )

    def return_routes_query(self) -> Select[DeclarativeMeta]:
        """Returns a query for routes.

        Returns:
            A query for routes."""

        return (
            select(Route)
            .distinct()
            .where(Route.route_id.in_(select(self.trip_query.columns.route_id)))
        )

    def get_vehicles(self, add_routes: list[str] = None) -> Select[DeclarativeMeta]:
        """Returns a query for vehicles.

        Args:
            add_routes (list[str], optional): list of routes to add to query for vehicles. \
                Defaults to None.
        Returns:
            A query for vehicles.
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
                    Vehicle.route_id.in_(add_routes or []),
                )
            )
        )

    def get_facilities(self, types: list[str] = None) -> Select[DeclarativeMeta]:
        """Returns a query for parking facilities.

        Args:
            types (list[str]): list of facility types, \
                default: ("parking-area", "bike-storage")
        Returns:
            A query for parking facilities.
        """
        return (
            select(Facility)
            .distinct()
            .where(
                Facility.stop_id.in_(select(self.parent_stops_query.columns.stop_id)),
                Facility.facility_type.in_(types or ("parking-area", "bike-storage")),
            )
        )
