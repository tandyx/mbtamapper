"""File to hold the Route class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

# pylint: disable=line-too-long

if TYPE_CHECKING:
    from .agency import Agency
    from .alert import Alert
    from .multi_route_trip import MultiRouteTrip
    from .prediction import Prediction
    from .trip import Trip
    from .vehicle import Vehicle


class Route(Base):
    """Route

    distinct from `Shape`, but mapped as such

    this is used to display stuff like "Red Line" or "1" with colors
    """

    __tablename__ = "routes"
    __filename__ = "routes.txt"

    route_id: Mapped[str] = mapped_column(primary_key=True)
    agency_id: Mapped[str] = mapped_column(
        ForeignKey("agencies.agency_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    route_short_name: Mapped[Optional[str]]
    route_long_name: Mapped[Optional[str]]
    route_desc: Mapped[Optional[str]]
    route_type: Mapped[Optional[str]]
    route_url: Mapped[Optional[str]]
    route_color: Mapped[Optional[str]]
    route_text_color: Mapped[Optional[str]]
    route_sort_order: Mapped[int]
    route_fare_class: Mapped[Optional[str]]
    line_id: Mapped[Optional[str]]
    listed_route: Mapped[Optional[str]]
    network_id: Mapped[Optional[str]]

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
        self.route_name = self.route_short_name or self.route_long_name
