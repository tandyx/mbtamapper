"""File to hold the Trip class and its associated methods."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase


class Trip(GTFSBase):
    """Trip"""

    __tablename__ = "trips"
    __filename__ = "trips.txt"

    route_id = mapped_column(
        String, ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id = mapped_column(
        String,
        ForeignKey("calendars.service_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    trip_id = mapped_column(String, primary_key=True)
    trip_headsign = mapped_column(String)
    trip_short_name = mapped_column(String)
    direction_id = mapped_column(Integer)
    block_id = mapped_column(String)
    shape_id = mapped_column(
        String, ForeignKey("shapes.shape_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_accessible = mapped_column(String)
    trip_route_type = mapped_column(String)
    route_pattern_id = mapped_column(String)
    bikes_allowed = mapped_column(Integer)

    calendar = relationship("Calendar", back_populates="trips")
    multi_route_trips = relationship(
        "MultiRouteTrip", back_populates="trip", passive_deletes=True
    )
    shape = relationship("Shape", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip", passive_deletes=True)
    # calendar = relationship("Calendar", back_populates="trips")
    route = relationship("Route", back_populates="trips")
    all_routes = relationship(
        "Route",
        primaryjoin="""or_(Trip.route_id==foreign(Route.route_id),
                    and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
                    foreign(Route.route_id)==MultiRouteTrip.added_route_id))""",
        viewonly=True,
    )
    predictions = relationship(
        "Prediction",
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Prediction.trip_id)",
        viewonly=True,
    )
    vehicle = relationship(
        "Vehicle",
        back_populates="trip",
        primaryjoin="Trip.trip_id==foreign(Vehicle.trip_id)",
        viewonly=True,
    )
    alerts = relationship(
        "Alert",
        back_populates="trip",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    DIRECTION_ID_MAPPER = {"0": "Outbound", "1": "Inbound"}

    def as_label(self) -> str:
        """Returns trip as label"""
        return f"{self.trip_short_name or self.trip_id}: {self.trip_headsign}"

    def return_direction(self) -> str:
        """Returns trip as label"""
        return self.DIRECTION_ID_MAPPER.get(str(self.direction_id), "Unknown")
