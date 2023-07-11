"""predictions"""
from dateutil.parser import isoparse
from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor, attributes
from gtfs_loader.gtfs_base import GTFSBase


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"

    id = Column(String, primary_key=True)
    attributes_arrival_time = Column(String)
    attributes_departure_time = Column(String)
    attributes_direction_id = Column(String)
    attributes_schedule_relationship = Column(String)
    attributes_status = Column(String)
    attributes_stop_sequence = Column(Integer)
    relationships_route_data_id = Column(String, ForeignKey("routes.route_id"))
    relationships_schedule_data_id = Column(String)
    relationships_stop_data_id = Column(String, ForeignKey("stops.stop_id"))
    relationships_trip_data_id = Column(String, ForeignKey("trips.trip_id"))
    relationships_vehicle_data_id = Column(String, ForeignKey("vehicles.vehicle_id"))

    @reconstructor
    def init_on_load(self):
        self.arrival_datetime = isoparse(self.attributes_arrival_time)
        self.departure_datetime = isoparse(self.attributes_departure_time)

    def return_column_names(self) -> list[str]:
        return [
            k
            for k, v in Prediction.__dict__.items()
            if isinstance(v, attributes.InstrumentedAttribute)
        ]

    def __repr__(self):
        return f"<Prediction(id={self.id})>"


print()
