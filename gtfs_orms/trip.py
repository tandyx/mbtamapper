"""File to hold the Trip class and its associated methods."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .alert import Alert
    from .calendar import Calendar
    from .multi_route_trip import MultiRouteTrip
    from .prediction import Prediction
    from .route import Route
    from .shape import Shape
    from .stop_time import StopTime
    from .vehicle import Vehicle


class Trip(GTFSBase):
    """Trip"""

    __tablename__ = "trips"
    __filename__ = "trips.txt"

    route_id: str = mapped_column(
        String, ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id: str = mapped_column(
        String,
        ForeignKey("calendars.service_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    trip_id: str = mapped_column(String, primary_key=True)
    trip_headsign: str = mapped_column(String)
    trip_short_name: str = mapped_column(String)
    direction_id: int = mapped_column(Integer)
    block_id: str = mapped_column(String)
    shape_id: str = mapped_column(
        String, ForeignKey("shapes.shape_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_accessible: str = mapped_column(String)
    trip_route_type: str = mapped_column(String)
    route_pattern_id: str = mapped_column(String)
    bikes_allowed: int = mapped_column(Integer)

    calendar: "Calendar" = relationship("Calendar", back_populates="trips")
    multi_route_trips: list["MultiRouteTrip"] = relationship(
        "MultiRouteTrip", back_populates="trip", passive_deletes=True
    )
    shape: "Shape" = relationship("Shape", back_populates="trips")
    stop_times: list["StopTime"] = relationship(
        "StopTime", back_populates="trip", passive_deletes=True
    )
    route: "Route" = relationship("Route", back_populates="trips")
    all_routes: list["Route"] = relationship(
        "Route",
        primaryjoin="""or_(Trip.route_id==foreign(Route.route_id),
                    and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
                    foreign(Route.route_id)==MultiRouteTrip.added_route_id))""",
        viewonly=True,
    )
    predictions: list["Prediction"] = relationship(
        "Prediction",
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Prediction.trip_id)",
        viewonly=True,
    )
    vehicle: "Vehicle" = relationship(
        "Vehicle",
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Vehicle.trip_id)",
        viewonly=True,
    )
    alerts: list["Alert"] = relationship(
        "Alert",
        back_populates="trip",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )
