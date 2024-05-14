"""File to hold the Trip class and its associated methods."""

from typing import TYPE_CHECKING, Optional, Union

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
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

    __tablename__ = "trips"
    __filename__ = "trips.txt"

    route_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("calendars.service_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    trip_id: Mapped[str] = mapped_column(primary_key=True)
    trip_headsign: Mapped[Optional[str]]
    trip_short_name: Mapped[Optional[str]]
    direction_id: Mapped[Optional[int]]
    block_id: Mapped[Optional[str]]
    shape_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("shapes.shape_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_accessible: Mapped[Optional[int]]
    trip_route_type: Mapped[Optional[str]]
    route_pattern_id: Mapped[Optional[str]]
    bikes_allowed: Mapped[Optional[int]]

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

    @property
    def destination(self) -> Union["Stop", None]:
        """the destination of the trip as a `stop`"""
        try:
            return max(self.stop_times).stop
        except (ValueError, TypeError, AttributeError):
            return None
