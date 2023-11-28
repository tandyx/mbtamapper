"""File to hold the Alert class and its associated methods."""
# pylint: disable=line-too-long
from dateutil.parser import isoparse

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor

from .gtfs_base import GTFSBase


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

    REALTIME_NAME = "service_alerts"

    @reconstructor
    def _init_on_load_(self):
        """Loads active_period_end and active_period_start as datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        self.url = self.url or "https://www.mbta.com/"
        self.end_datetime = (
            isoparse(self.active_period_end) if self.active_period_end else None
        )
        self.start_datetime = (
            isoparse(self.active_period_start) if self.active_period_start else None
        )
        self.updated_at_datetime = isoparse(self.timestamp)

    def as_html(self) -> str:
        """Returns alert as html."""
        return (
            f"<tr><td href = '{self.url}' target='_blank'>{str(self.header)}</td>"
            f"<td>{self.updated_at_datetime.strftime('%m/%d/%Y %I:%M %p')}</td>"  # pylint: disable=no-member
            "</tr>"
        )
