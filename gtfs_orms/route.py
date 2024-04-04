"""File to hold the Route class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

# pylint: disable=line-too-long

if TYPE_CHECKING:
    from .agency import Agency
    from .alert import Alert
    from .multi_route_trip import MultiRouteTrip
    from .prediction import Prediction
    from .trip import Trip
    from .vehicle import Vehicle


class Route(GTFSBase):
    """Route"""

    __tablename__ = "routes"
    __filename__ = "routes.txt"

    route_id: str = mapped_column(String, primary_key=True)
    agency_id: Optional[str] = mapped_column(
        String, ForeignKey("agencies.agency_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    route_short_name: Optional[str] = mapped_column(String)
    route_long_name: Optional[str] = mapped_column(String)
    route_desc: Optional[str] = mapped_column(String)
    route_type: Optional[str] = mapped_column(String)
    route_url: Optional[str] = mapped_column(String)
    route_color: Optional[str] = mapped_column(String)
    route_text_color: Optional[str] = mapped_column(String)
    route_sort_order: Optional[int] = mapped_column(Integer)
    route_fare_class: Optional[str] = mapped_column(String)
    line_id: Optional[str] = mapped_column(String)
    listed_route: Optional[str] = mapped_column(String)
    network_id: Optional[str] = mapped_column(String)

    agency: "Agency" = relationship("Agency", back_populates="routes")
    multi_route_trips: list["MultiRouteTrip"] = relationship(
        "MultiRouteTrip", back_populates="route", passive_deletes=True
    )
    trips: list["Trip"] = relationship(
        "Trip", back_populates="route", passive_deletes=True
    )
    all_trips: list["Trip"] = relationship(
        "Trip",
        primaryjoin="""or_(
            foreign(Trip.route_id)==Route.route_id, 
            and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
            Route.route_id==foreign(MultiRouteTrip.added_route_id))
            )""",
        viewonly=True,
    )
    predictions: list["Prediction"] = relationship(
        "Prediction",
        back_populates="route",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    vehicles: list["Vehicle"] = relationship(
        "Vehicle",
        back_populates="route",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    alerts: list["Alert"] = relationship(
        "Alert",
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
