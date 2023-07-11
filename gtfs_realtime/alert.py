"""Alerts"""

from dateutil.parser import isoparse
from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Alert(GTFSBase):
    """Alerts"""

    __tablename__ = "alerts"

    alert_id = Column(String)
    alert_type = Column(String)
    banner = Column(String)
    cause = Column(String)
    created_at = Column(String)
    description = Column(String)
    effect = Column(String)
    header = Column(String)
    lifecycle = Column(String)
    service_effect = Column(String)
    severity = Column(String)
    short_header = Column(String)
    timeframe = Column(String)
    updated_at = Column(String)
    url = Column(String)
    links_self = Column(String)
    active_period_end = Column(String)
    active_period_start = Column(String)
    direction_id = Column(String)
    route_id = Column(String)
    route_type = Column(String)
    trip_id = Column(String)
    stop_id = Column(String)
    index = Column(Integer, primary_key=True)

    route = relationship(
        "Route",
        back_populates="alerts",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="alerts",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="alerts",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    DATETIME_MAPPER = {
        "active_period_end": "end_datetime",
        "active_period_start": "start_datetime",
        "created_at": "created_at_datetime",
        "updated_at": "updated_at_datetime",
    }

    @reconstructor
    def init_on_load(self):
        """Loads active_period_end and active_period_start as datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        for key, value in self.DATETIME_MAPPER.items():
            if getattr(self, key, None):
                setattr(self, value, isoparse(getattr(self, key)))

    def __repr__(self):
        return f"<Alert(id={self.alert_id})>"
