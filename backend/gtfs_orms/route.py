"""File to hold the Route class and its associated methods."""

import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

# pylint: disable=line-too-long

if t.TYPE_CHECKING:
    from .agency import Agency
    from .alert import Alert
    from .calendar import Calendar
    from .multi_route_trip import MultiRouteTrip
    from .prediction import Prediction
    from .stop_time import StopTime
    from .trip import Trip
    from .vehicle import Vehicle


class Route(Base):
    """Route

    distinct from `Shape`, but mapped as such

    this is used to display stuff like "Red Line" or "1" with colors

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#routestxt
    """

    __tablename__ = "route"
    __filename__ = "routes.txt"

    route_id: Mapped[str] = mapped_column(primary_key=True)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agency.agency_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    route_short_name: Mapped[t.Optional[str]]
    route_long_name: Mapped[t.Optional[str]]
    route_desc: Mapped[str]
    route_type: Mapped[str]
    route_url: Mapped[t.Optional[str]]
    route_color: Mapped[str]
    route_text_color: Mapped[str]
    route_sort_order: Mapped[int]
    route_fare_class: Mapped[str]
    line_id: Mapped[t.Optional[str]]
    listed_route: Mapped[t.Optional[bool]]
    network_id: Mapped[str]

    agency: Mapped["Agency"] = relationship(back_populates="routes")
    multi_route_trips: Mapped[list["MultiRouteTrip"]] = relationship(
        back_populates="route", passive_deletes=True
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="route", passive_deletes=True
    )
    all_trips: Mapped[list["Trip"]] = relationship(
        primaryjoin="""or_(
            foreign(Trip.route_id)==Route.route_id, 
            and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
            Route.route_id==foreign(MultiRouteTrip.added_route_id))
            )""",
        viewonly=True,
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="route",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="route",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="route",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database."""
        # pylint: disable=attribute-defined-outside-init
        self.route_url = (
            self.route_url or f"https://www.mbta.com/schedules/{self.route_id}"
        )
        self.route_name = (self.route_short_name or self.route_long_name).replace(
            "/", " / "
        )

    def get_stop_times(self) -> t.Generator["StopTime", None, None]:
        """returns a generator of stop time objects by yielding trips"""
        for trip in self.trips:
            yield from trip.stop_times

    @property
    def calendars(self) -> set["Calendar"]:
        """returns unique set of calendars for the route"""
        return {trip.calendar for trip in self.trips}

    @t.override
    def as_json(self, *include: str, **kwargs) -> dict[str, t.Any]:
        """returns `Stop(...)` as a json serializable object:

        args:
            include: other orms/attars to include
            kwargs: unused \n
        returns:
            dict[str, Any]: json object of stop
        """
        json_dict = super().as_json(*include, **kwargs)
        calendars = self.calendars
        if "stop_times" in include:
            json_dict["stop_times"] = [st.as_json() for st in self.get_stop_times()]
        if "start_date" in include:
            json_dict["start_date"] = min(c.start_date.timestamp() for c in calendars)
        if "end_date" in include:
            json_dict["end_date"] = max(c.end_date.timestamp() for c in calendars)
        if "calendars" in include:
            json_dict["calendars"] = [c.as_json() for c in self.calendars]
        return json_dict
