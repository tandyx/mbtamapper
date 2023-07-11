"""Vehicle"""
from datetime import datetime
import pytz
from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor

from shapely.geometry import Point
from geojson import Feature

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

    next_stop_prediction = relationship(
        "Prediction",
        primaryjoin="""and_(foreign(Vehicle.vehicle_id)==Prediction.vehicle_id,
                            foreign(Vehicle.stop_id)==Prediction.stop_id)""",
        viewonly=True,
    )

    DATETIME_MAPPER = {"updated_at": "updated_at_datetime"}

    DIRECTION_MAPPER = {"0": "Outbound", "1": "Inbound"}

    @reconstructor
    def init_on_load(self):
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.updated_at_datetime = isoparse(self.updated_at)

    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id})>"

    def return_current_status(self) -> str:
        """Returns current status of vehicle."""
        current_status = (
            self.current_status.lower().replace("_", " ")
            + " "
            + self.stop.stop_name
            + f""" (in {int(((self.next_stop_prediction.predicted or self.next_stop_prediction.scheduled) - datetime.now(pytz.timezone(self.route.agency.agency_timezone))).total_seconds() / 60)} minutes)"""
        )

        return current_status

    def as_point(self) -> Point:
        """Returns vehicle as point."""
        return Point(self.longitude, self.latitude)

    def as_dict(self) -> dict[str]:
        """Returns vehicle as dict."""

        return {
            "label": self.label or self.vehicle_id,
            "trip": self.trip.trip_short_name or self.trip.trip_headsign,
            "direction": self.DIRECTION_MAPPER.get(self.direction_id, "Unknown"),
            "vehicle_type": self.vehicle_type,
            "bearing": self.bearing,
            "current_status": self.return_current_status(),
            "current_stop_sequence": self.current_stop_sequence,
            "direction_id": self.direction_id,
            "occupancy_status": self.occupancy_status,
            "speed": self.speed,
            "updated_at": self.updated_at_datetime.strftime("%m/%d/%Y %I:%M%p"),
            "alerts": [a.as_dict() for a in self.trip.alerts],
            "predictions": [prediction.as_dict() for prediction in self.predictions],
        }

    def as_feature(self) -> Feature:
        """Returns vehicle as feature."""

        return Feature(geometry=self.as_point(), properties=self.as_dict())
