"""File to hold the Alert class and its associated methods."""

from dateutil.parser import isoparse
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase


class Alert(GTFSBase):
    """Alerts"""

    __tablename__ = "alerts"
    __realtime_name__ = "service_alerts"

    alert_id = mapped_column(String)
    cause = mapped_column(String)
    effect = mapped_column(String)
    severity = mapped_column(String)
    stop_id = mapped_column(String)
    agency_id = mapped_column(String)
    route_id = mapped_column(String)
    route_type = mapped_column(String)
    direction_id = mapped_column(String)
    trip_id = mapped_column(String)
    active_period_end = mapped_column(String)
    header = mapped_column(String)
    description = mapped_column(String)
    url = mapped_column(String)
    active_period_start = mapped_column(String)
    timestamp = mapped_column(String)
    index = mapped_column(Integer, primary_key=True)

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
            f"<td>{self.updated_at_datetime.strftime('%m/%d/%Y %I:%M %p')}</td>"
            "</tr>"
        )
