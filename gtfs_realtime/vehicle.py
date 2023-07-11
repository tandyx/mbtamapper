"""Vehicle"""
from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"

    vehicle_id = Column(String, primary_key=True)
    vehicle_type = Column(String)
    bearing = Column(Float)
    current_status = Column(String)
    current_stop_sequence = Column(Integer)
    direction_id = Column(String)
    label = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    occupancy_status = Column(String)
    speed = Column(Float)
    updated_at = Column(String)
    links_self = Column(String)
    route_id = Column(String)
    stop_id = Column(String)
    trip_id = Column(String)

    predictions = relationship(
        "Prediction",
        back_populates="vehicle",
        primaryjoin="Vehicle.vehicle_id==foreign(Prediction.vehicle_id)",
        viewonly=True,
    )
    route = relationship(
        "Route",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="vehicle",
        primaryjoin="foreign(Vehicle.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    DATETIME_MAPPER = {
        "updated_at": "updated_at_datetime",
    }

    @reconstructor
    def init_on_load(self):
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        for key, value in self.DATETIME_MAPPER.items():
            if getattr(self, key, None):
                setattr(self, value, isoparse(getattr(self, key)))

    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id})>"
