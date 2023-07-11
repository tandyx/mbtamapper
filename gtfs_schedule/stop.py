"""File to hold the Calendar class and its associated methods."""
from shapely.geometry import Point
from geojson import Feature

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Float, ForeignKey
from gtfs_loader.gtfs_base import GTFSBase


class Stop(GTFSBase):
    """Stop"""

    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True)
    stop_code = Column(String)
    stop_name = Column(String)
    stop_desc = Column(String)
    platform_code = Column(String)
    platform_name = Column(String)
    stop_lat = Column(Float)
    stop_lon = Column(Float)
    zone_id = Column(String)
    stop_address = Column(String)
    stop_url = Column(String)
    level_id = Column(String)
    location_type = Column(String)
    parent_station = Column(String, ForeignKey("stops.stop_id"))
    wheelchair_boarding = Column(String)
    municipality = Column(String)
    on_street = Column(String)
    at_street = Column(String)
    vehicle_type = Column(String)

    stop_times = relationship("StopTime", back_populates="stop", passive_deletes=True)
    to_stop_transfers = relationship(
        "Transfer",
        back_populates="to_stop",
        foreign_keys="Transfer.to_stop_id",
        passive_deletes=True,
    )
    from_stop_transfers = relationship(
        "Transfer",
        back_populates="from_stop",
        foreign_keys="Transfer.from_stop_id",
        passive_deletes=True,
    )
    facilities = relationship("Facility", back_populates="stop", passive_deletes=True)
    parent_stop = relationship(
        "Stop", primaryjoin="foreign(Stop.parent_station)==remote(Stop.stop_id)"
    )
    predictions = relationship(
        "Prediction",
        back_populates="stop",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    vehicles = relationship(
        "Vehicle",
        back_populates="stop",
        primaryjoin="Stop.stop_id==foreign(Vehicle.stop_id)",
        viewonly=True,
    )
    alerts = relationship(
        "Alert",
        back_populates="stop",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    exclude_keys = [
        "_sa_instance_state",
        "parent_station",
        "stop_times",
        "facilities",
        "parent_stop",
    ]

    def __repr__(self):
        return f"<Stop(stop_id={self.stop_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the stop"""
        return Point(self.stop_lon, self.stop_lat)

    def as_feature(self) -> Feature:
        """Returns stop object as a feature."""

        properties = {
            "stop_id": self.stop_id,
            "stop_name": self.stop_name,
            "stop_desc": self.stop_desc,
            "platform_code": self.platform_code,
            "platform_name": self.platform_name,
            "zone_id": self.zone_id,
            "stop_address": self.stop_address,
            "stop_url": self.stop_url,
            "level_id": self.level_id,
            "location_type": self.location_type,
            "parent_station": self.parent_station,
            "wheelchair_boarding": self.wheelchair_boarding,
            "municipality": self.municipality,
            "on_street": self.on_street,
            "at_street": self.at_street,
            "vehicle_type": self.vehicle_type,
            "alerts": [alert.as_dict() for alert in self.alerts],
            "predictions": [prediction.as_dict() for prediction in self.predictions],
        }

        feature = Feature(
            id=self.stop_id, geometry=self.as_point(), properties=properties
        )

        return feature
