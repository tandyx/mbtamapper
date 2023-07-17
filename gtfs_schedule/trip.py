"""File to hold the Calendar class and its associated methods."""
from sqlalchemy import Integer, ForeignKey, Column, String
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Trip(GTFSBase):
    """Trip"""

    __tablename__ = "trips"

    route_id = Column(
        String, ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id = Column(
        String,
        ForeignKey("calendars.service_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    trip_id = Column(String, primary_key=True)
    trip_headsign = Column(String)
    trip_short_name = Column(String)
    direction_id = Column(Integer)
    block_id = Column(String)
    shape_id = Column(String, ForeignKey("shapes.shape_id"))
    wheelchair_accessible = Column(String)
    trip_route_type = Column(String)
    route_pattern_id = Column(String)
    bikes_allowed = Column(Integer)

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

    @reconstructor
    def init_on_load(self) -> None:
        """Post-load initialization"""
        # pylint: disable=attribute-defined-outside-init
        self.is_added = bool(self.multi_route_trips)
        self.active = bool(self.predictions)
        # self.trip_start_seconds = min(
        #     to_seconds(stop_time.departure_time) for stop_time in self.stop_times
        # )
        # self.origin_stop_time = min(self.stop_times, key=lambda x: x.stop_sequence)
        # self.destination_stop_time = max(self.stop_times, key=lambda x: x.stop_sequence)

    def __repr__(self) -> str:
        return f"<Trip(trip_id={self.trip_id})>"

    def as_label(self) -> str:
        """Returns trip as label"""
        return f"{self.trip_short_name or self.trip_id}: {self.trip_headsign}"

    def return_direction(self) -> str:
        """Returns trip as label"""
        return self.DIRECTION_ID_MAPPER.get(str(self.direction_id), "Unknown")

    def return_trip_start_time(self) -> str:
        """Returns trip as label"""
