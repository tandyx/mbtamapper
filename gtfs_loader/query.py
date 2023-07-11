from datetime import datetime
from sqlalchemy import or_, not_, and_
from sqlalchemy.sql import selectable, select

from gtfs_schedule import *


class Query:
    """Class to store query information for GTFS data.

    Args:
        route_type (str): A comma separated string of route types to query.
    """

    def __init__(self, route_type: str):
        self.route_type = route_type.split(",")
        self.mrt_query = self.return_mrt_query()
        self.base_stop_query = self.return_base_stop_query()
        self.parent_stops_query = self.return_parent_stops_query()
        self.platform_stops_query = self.return_platform_stops_query()

    def __repr__(self) -> str:
        return f"<Query(route_type={self.route_type})>"

    def return_mrt_query(self) -> selectable.Select:
        """Returns query for multi route trips"""
        mrt_subquery = (
            select(Trip)
            .join(Route, Trip.route_id == Route.route_id)
            .where(Route.route_type.in_(self.route_type))
            .subquery()
        )

        mrt_query = (
            select(MultiRouteTrip)
            .join(Route, MultiRouteTrip.added_route_id.in_(self.route_type))
            .outerjoin(
                mrt_subquery, MultiRouteTrip.trip_id == mrt_subquery.columns.trip_id
            )
            .where(
                Route.route_type.in_(self.route_type),
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
                    Stop.vehicle_type.in_(self.route_type),
                )
            )
        )

        return platform_stops

    def return_all_calendars_query(self, date: datetime) -> selectable.Select:
        """Returns query for all calendars

        Args:
            date (datetime): Date to query for."""
        all_calendars = select(Calendar).where(
            Calendar.service_id.in_(
                (
                    select(Calendar.service_id)
                    .distinct()
                    .join(Trip, Trip.service_id == Calendar.service_id)
                    .join(
                        CalendarAttribute,
                        Calendar.service_id == CalendarAttribute.service_id,
                    )
                    .join(Route, Trip.route_id == Route.route_id)
                    .where(
                        not_(
                            or_(
                                Calendar.start_date > date.strftime("%Y%m%d"),
                                Calendar.end_date < date.strftime("%Y%m%d"),
                                CalendarAttribute.service_schedule_typicality == "6",
                            )
                        ),
                        or_(
                            Route.route_type.in_(self.route_type),
                            Trip.trip_id.in_(select(self.mrt_query.columns.trip_id)),
                        ),
                    )
                )
            )
        )

        return all_calendars

    def return_active_calendars_query(self, date: datetime) -> selectable.Select:
        """Returns query for active calendars

        Args:
            date (datetime): Date to query for."""

        cal_stmt = (
            select(Calendar)
            .join(
                CalendarDate,
                Calendar.service_id == CalendarDate.service_id,
                isouter=True,
            )
            .where(
                or_(
                    and_(
                        Calendar.start_date <= date.strftime("%Y%m%d"),
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
                    ),
                )
            )
        )

        return cal_stmt
