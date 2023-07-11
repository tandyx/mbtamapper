"""File to hold the Calendar class and its associated methods."""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import shapely.ops
from shapely.geometry import LineString

from sqlalchemy import Integer, ForeignKey, Column, String
from sqlalchemy.orm import relationship, reconstructor

from shared_code.gtfs_helper_time_functions import seconds_to_iso
from gtfs_loader.gtfs_base import GTFSBase


class Trip(GTFSBase):
    """Trip"""

    __tablename__ = "trips"

    route_id = Column(
        String, ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    service_id = Column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
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

    multi_route_trips = relationship(
        "MultiRouteTrip", back_populates="trip", passive_deletes=True
    )
    shape = relationship("Shape", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip", passive_deletes=True)
    calendar = relationship("Calendar", back_populates="trips")
    route = relationship("Route", back_populates="trips")
    to_trip_transfers = relationship(
        "Transfer",
        back_populates="to_trip",
        foreign_keys="Transfer.to_trip_id",
        passive_deletes=True,
    )
    from_trip_transfers = relationship(
        "Transfer",
        back_populates="from_trip",
        foreign_keys="Transfer.from_trip_id",
        passive_deletes=True,
    )
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

    TRIP_FIELD_MAPPING = {
        "trip_headsign": "headsign",
        "direction_id": "direction",
        "trip_id": "externaltripid",
        "trip_short_name": "shortname",
    }

    @reconstructor
    def init_on_load(self) -> None:
        """Post-load initialization"""
        # pylint: disable=attribute-defined-outside-init
        self.is_added = bool(self.multi_route_trips)
        self.origin_stop_time = min(self.stop_times, key=lambda x: x.stop_sequence)
        self.destination_stop_time = max(self.stop_times, key=lambda x: x.stop_sequence)

    def __repr__(self) -> str:
        return f"<Trip(trip_id={self.trip_id})>"
