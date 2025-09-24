"""File to hold the Trip class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from ..helper_functions import get_date
from .base import Base

if t.TYPE_CHECKING:
    from .alert import Alert
    from .calendar import Calendar
    from .multi_route_trip import MultiRouteTrip
    from .prediction import Prediction
    from .route import Route
    from .shape import Shape
    from .stop import Stop
    from .stop_time import StopTime
    from .transfer import Transfer
    from .trip_property import TripProperty
    from .vehicle import Vehicle


class Trip(Base):
    """Trip

    each trip is the equivalent to a "train" (such as 808)

    note that not all Predictions have a scheduled Trip

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#tripstxt

    """

    __tablename__ = "trip"
    __filename__ = "trips.txt"

    route_id: Mapped[str] = mapped_column(
        ForeignKey("route.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id: Mapped[str] = mapped_column(
        ForeignKey("calendar.service_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    trip_id: Mapped[str] = mapped_column(primary_key=True)
    trip_headsign: Mapped[str]
    trip_short_name: Mapped[t.Optional[str]]
    direction_id: Mapped[int]
    block_id: Mapped[t.Optional[str]]
    shape_id: Mapped[str] = mapped_column(
        ForeignKey("shape.shape_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_accessible: Mapped[int]
    trip_route_type: Mapped[t.Optional[str]]
    route_pattern_id: Mapped[str]
    bikes_allowed: Mapped[int]

    calendar: Mapped["Calendar"] = relationship(back_populates="trips")
    multi_route_trips: Mapped[list["MultiRouteTrip"]] = relationship(
        back_populates="trip", passive_deletes=True
    )
    shape: Mapped["Shape"] = relationship(back_populates="trips")
    stop_times: Mapped[list["StopTime"]] = relationship(
        back_populates="trip", passive_deletes=True
    )
    route: Mapped["Route"] = relationship(back_populates="trips")

    trip_properties: Mapped[list["TripProperty"]] = relationship(
        back_populates="trip", passive_deletes=True
    )

    all_routes: Mapped[list["Route"]] = relationship(
        primaryjoin="""or_(Trip.route_id==foreign(Route.route_id),
                    and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
                    foreign(Route.route_id)==MultiRouteTrip.added_route_id))""",
        viewonly=True,
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Prediction.trip_id)",
        viewonly=True,
    )
    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Vehicle.trip_id)",
        viewonly=True,
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="trip",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    to_trip_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="to_trip",
        foreign_keys="Transfer.to_trip_id",
        passive_deletes=True,
    )
    from_trip_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="from_trip",
        foreign_keys="Transfer.from_trip_id",
        passive_deletes=True,
    )

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database."""
        # pylint: disable=attribute-defined-outside-init
        self.active = self.is_active()

    @property
    def destination(self) -> "Stop | None":
        """the destination of the trip as a `stop`"""
        return getattr(max(self.stop_times, default=None), "stop", None)

    def is_active(self, _date: dt.datetime | None = None, **kwargs) -> bool:
        """Returns true if this `Trip` is active on the given date and time

        args:
            date (datetime = None): the date to check <- defaults to the current date
            kwargs: additional arguments passed to `get_date` \n
        returns:
            bool: whether the stop is active on the given date and time
        """
        return self.calendar.operates_on(_date or get_date(**kwargs))

    # @property
    # def active(self) -> bool:
    #     """wrapper for self.is_active"""
    #     return self.is_active(get_date())
