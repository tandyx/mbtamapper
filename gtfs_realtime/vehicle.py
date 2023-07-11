from dateutil.parser import isoparse
from sqlalchemy import ForeignKey, Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Vehicle(GTFSBase):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True)
    attributes_bearing = Column(Float)
    attributes_current_status = Column(String)
    attributes_current_stop_sequence = Column(Integer)
    attributes_direction_id = Column(String)
    attributes_label = Column(String)
    attributes_latitude = Column(Float)
    attributes_longitude = Column(Float)
    attributes_occupancy_status = Column(String)
    attributes_speed = Column(Float)
    attributes_updated_at = Column(String)
    relationships_route_data_id = Column(String, ForeignKey("routes.route_id"))
    relationships_stop_data_id = Column(String, ForeignKey("stops.stop_id"))
    relationships_trip_data_id = Column(String, ForeignKey("trips.trip_id"))

    predictions = relationship("Prediction", back_populates="vehicle")
    route = relationship("Route", back_populates="vehicles")
    stop = relationship("Stop", back_populates="vehicles")
    trip = relationship("Trip", back_populates="vehicle")


[
    "id",
    "type",
    "attributes_bearing",
    "attributes_current_status",
    "attributes_current_stop_sequence",
    "attributes_direction_id",
    "attributes_label",
    "attributes_latitude",
    "attributes_longitude",
    "attributes_occupancy_status",
    "attributes_speed",
    "attributes_updated_at",
    "links_self",
    "relationships_route_data_id",
    "relationships_route_data_type",
    "relationships_stop_data_id",
    "relationships_stop_data_type",
    "relationships_trip_data_id",
    "relationships_trip_data_type",
]
