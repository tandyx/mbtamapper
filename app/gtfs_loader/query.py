"""Defines a class to hold and generate queries."""

# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# pylint: disable=no-self-argument
import datetime as dt
import typing as t

from sqlalchemy.orm import aliased
from sqlalchemy.sql import *

from gtfs_orms import *
from helper_functions import classproperty


class Query:
    """
    Class to hold and generate queries. \n
    Called with `Query(r1, r2, ...)`

    Args:
        - `*route_types (str)`: list of route_types to query
    """

    @classproperty
    def ferry_parking_query(cls: t.Type[t.Self]) -> Select[tuple[Base]]:
        """
        Returns a query for ferry parking.

        Returns:
            - `Select[tuple[Base]]`: A query for ferry parking.
        """
        return (
            select(Facility)
            .join(Stop, Facility.stop_id == Stop.stop_id)
            .where(Stop.vehicle_type == "4")
            .where(Facility.facility_type == "parking-area")
        )

    @staticmethod
    def select(*orms: Base, **kwargs) -> Select[tuple[Base]]:
        """
        Returns a generic select query for tables.

        Args:
            - `*orms`: tables to query
            - `**kwargs`: kwargs for select\n
        Returns:
            - `Select[tuple[Base]]`: A generic select query for tables.
        """
        return select(*orms, **kwargs)

    @staticmethod
    def delete(orm: Base) -> Delete:
        """
        Returns a generic delete query for a table.

        args:
            - `orm (Base)`: table to query\n
        Returns:
            - `Delete`: A generic delete query for a table.
        """
        return delete(orm)

    @staticmethod
    def update(orm: Base) -> Update:
        """
        Returns a generic update query for a table.

        args:
            - `orm (Base)`: table to query\n
        returns:
            - `Update`: A generic update query for a table.
        """
        return update(orm)

    @staticmethod
    def get_active_calendars_query(
        date: dt.datetime, specific: bool = False, days_ahead: int = 7
    ) -> Select[tuple[Base]]:
        """
        Returns a query for active calendars on a date.

        Args:
            - `date (datetime)`: date to query
            - `specific (bool, optional)`: whether to query for specific date. \
                Defaults to False (query for week)
            - `days_ahead (int, optional)`: number of days ahead to query. Defaults to 7.\n
        Returns:
            - `Select[tuple[Base]]`: A query for active calendars on a date.
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
                            <= (date + dt.timedelta(days=7)).strftime("%Y%m%d"),
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
                        <= (date + dt.timedelta(days=days_ahead)).strftime("%Y%m%d"),
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
    def delete_calendars_query(*args, **kwargs) -> Delete:
        """
        Returns a query to delete calendars.

        Args:
            - `*args`: args for get_active_calendars_query
            - `**kwargs`: kwargs for get_active_calendars_query \n
        Returns:
            - `Delete`: A query to delete calendars.
        """

        return delete(Calendar).where(
            Calendar.service_id.notin_(
                select(
                    __class__.get_active_calendars_query(
                        *args, **kwargs
                    ).columns.service_id
                )
            )
        )

    @staticmethod
    def delete_facilities_query(*exclude: str) -> Delete:
        """Returns a query to delete facilities.

        Args:
            - `*exclude (str)`: list of facility types to exclude.
        Returns:
            - `Select[tuple[Base]]`: A query to delete facilities.
        """

        return delete(Facility).where(
            Facility.facility_id.not_in(
                select(Facility.facility_id).where(
                    Facility.facility_type.in_(exclude), Facility.stop_id.isnot(None)
                )
            )
        )

    @staticmethod
    def get_shapes_from_route_query(*routes: str) -> Select[tuple[Base]]:
        """Returns a query for shapes.

        Args:
            - `*routes (str)`: list of routes to query. Defaults to None.\n
        Returns:
            - `Select[tuple[Base]]`: A query for shapes.
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
    def get_dataset_query(realtime_name: str) -> Select[tuple[Base]]:
        """Returns a query for linked dataset.

        Args:
            - `realtime_name (str)`: realtime name\n
        Returns:
            - `Select[tuple[Base]]`: A query for linked dataset."""
        return select(LinkedDataset).where(getattr(LinkedDataset, realtime_name))

    @staticmethod
    def get_item_by_attr_query(
        orm: t.Type[Base], param: str, param_value: Any
    ) -> Select[tuple[Base]]:
        """Returns a query for an item by id.

        Args:
            - `orm (t.Type[Base])`: table to query \n
        Returns:
            - `Select[tuple[Base]]`: A query for an item by id.
        """
        return select(orm).where(getattr(orm, param) == param_value)

    def __init__(self, *route_types: str) -> None:
        """Initializes Query, called with Query(r1, r2, ...)

        Args:
            - `*route_types (str)`: list of route_types to query
        """
        self.route_types = route_types
        self.trip_query = self._get_trips_query()
        self.parent_stops_query = self._get_parent_stops_query()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(route_types={', '.join(self.route_types)})>"

    def __str__(self) -> str:
        return self.__repr__()

    def _get_trips_query(self) -> Select[tuple[Base]]:
        """Returns a query for trips.

        Returns:
            - `Select[tuple[Base]]`: A query for trips."""
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

    def _get_parent_stops_query(self) -> Select[tuple[Base]]:
        """Returns a query for parent stops.

        Returns:
            - `Select[tuple[Base]]`: A query for parent stops.
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

    def get_shapes_query(self) -> Select[tuple[Base]]:
        """Returns a query for shapes.

        Returns:
            - `Select[tuple[Base]]`: A query for shapes."""
        return (
            select(Shape)
            .distinct()
            .join(Trip, Shape.shape_id == Trip.shape_id)
            .where(Trip.trip_id.in_(select(self.trip_query.columns.trip_id)))
        )

    def get_routes_query(self) -> Select[tuple[Base]]:
        """Returns a query for routes.

        Returns:
            - `Select[tuple[Base]]`: A query for routes."""

        return (
            select(Route)
            .distinct()
            .where(Route.route_id.in_(select(self.trip_query.columns.route_id)))
        )

    def get_vehicles_query(self, *add_routes: str) -> Select[tuple[Base]]:
        """Returns a query for vehicles.

        Args:
            - `*add_routes (str, optional)`: list of routes to add to query for vehicles. \
                Defaults to `None`. \n
        Returns:
            - `Select[tuple[Base]]`: A query for vehicles.
        """

        return (
            select(Vehicle)
            .distinct()
            .join(Route, Vehicle.route_id == Route.route_id)
            .where(
                or_(
                    Vehicle.route_id.in_(
                        select(self.get_routes_query().columns.route_id)
                    ),
                    Vehicle.trip_id.in_(select(self.trip_query.columns.trip_id)),
                    Vehicle.route_id.in_(add_routes or tuple()),
                )
            )
        )

    def get_facilities_query(self, *types: str) -> Select[tuple[Base]]:
        """Returns a query for parking facilities.

        Args:
            - `*types (str)`: list of facility types, \n
        Returns:
            - `Select[tuple[Base]]`: A query for parking facilities.
        """
        return (
            select(Facility)
            .distinct()
            .where(
                Facility.stop_id.in_(select(self.parent_stops_query.columns.stop_id)),
                Facility.facility_type.in_(types),
            )
        )
