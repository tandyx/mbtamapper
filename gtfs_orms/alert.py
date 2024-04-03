"""File to hold the Alert class and its associated methods."""

from typing import TYPE_CHECKING

from dateutil.parser import isoparse
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .trip import Trip


class Alert(GTFSBase):
    """Alerts"""

    __tablename__ = "alerts"
    __realtime_name__ = "service_alerts"

    alert_id: str = mapped_column(String)
    cause: str = mapped_column(String)
    effect: str = mapped_column(String)
    severity: str = mapped_column(String)
    stop_id: str = mapped_column(String)
    agency_id: str = mapped_column(String)
    route_id: str = mapped_column(String)
    route_type: str = mapped_column(String)
    direction_id: str = mapped_column(String)
    trip_id: str = mapped_column(String)
    active_period_end: str = mapped_column(String)
    header: str = mapped_column(String)
    description: str = mapped_column(String)
    url: str = mapped_column(String)
    active_period_start: str = mapped_column(String)
    timestamp: str = mapped_column(String)
    index: int = mapped_column(Integer, primary_key=True)

    route: "Route" = relationship(
        "Route",
        back_populates="alerts",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )
    trip: "Trip" = relationship(
        "Trip",
        back_populates="alerts",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    stop: "Stop" = relationship(
        "Stop",
        back_populates="alerts",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

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
