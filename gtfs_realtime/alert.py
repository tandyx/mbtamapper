"""Alerts"""
# pylint: disable=line-too-long
from dateutil.parser import isoparse

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor

from gtfs_loader.gtfs_base import GTFSBase


class Alert(GTFSBase):
    """Alerts"""

    __tablename__ = "alerts"

    alert_id = Column(String)
    cause = Column(String)
    effect = Column(String)
    severity = Column(String)
    stop_id = Column(String)
    agency_id = Column(String)
    route_id = Column(String)
    route_type = Column(String)
    direction_id = Column(String)
    trip_id = Column(String)
    active_period_end = Column(String)
    header = Column(String)
    description = Column(String)
    url = Column(String)
    active_period_start = Column(String)
    timestamp = Column(String)
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
        "timestamp": "updated_at_datetime",
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

    def as_html(self):
        """Returns alert as html."""
        return (
            f"<tr><td href = '{self.url}' target='_blank'  style='text-decoration:none;'>{str(self.header)}</td>"
            f"<td>{self.updated_at_datetime.strftime('%m/%d/%Y %I:%M %p')}</td>"  # pylint: disable=no-member
            "</tr>"
        )
