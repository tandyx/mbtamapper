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
    from .vehicle import Vehicle


class Trip(Base):
    """Trip"""

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

    @property
    def destination(self) -> Union["Stop", None]:
        """the destination of the trip as a `stop`"""
        if not (dest := max(self.stop_times, default=None)):
            return None
        return dest.stop

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
