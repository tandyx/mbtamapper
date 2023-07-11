"""Alerts"""

from dateutil.parser import isoparse
from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Alert(GTFSBase):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)
    attributes_banner = Column(String)
    attributes_cause = Column(String)
    attributes_created_at = Column(String)
    attributes_description = Column(String)
    attributes_effect = Column(String)
    attributes_header = Column(String)
    attributes_lifecycle = Column(String)
    attributes_service_effect = Column(String)
    attributes_severity = Column(Integer)
    attributes_short_header = Column(String)
    attributes_timeframe = Column(String)
    attributes_updated_at = Column(String)
    attributes_url = Column(String)
    relationships_trips_data_id = Column(String, ForeignKey("trips.trip_id"))


[
    "id",
    "type",
    "attributes_banner",
    "attributes_cause",
    "attributes_created_at",
    "attributes_description",
    "attributes_effect",
    "attributes_header",
    "attributes_lifecycle",
    "attributes_service_effect",
    "attributes_severity",
    "attributes_short_header",
    "attributes_timeframe",
    "attributes_updated_at",
    "attributes_url",
    "links_self",
    "relationships_trips_data",
    "relationships_routes_data_id",
    "relationships_routes_data_type",
    "attributes_active_period_end",
    "attributes_active_period_start",
    "attributes_informed_entity_activities",
    "attributes_informed_entity_route",
    "attributes_informed_entity_route_type",
    "attributes_informed_entity_stop",
    "attributes_informed_entity_direction_id",
    "attributes_informed_entity_trip",
]
