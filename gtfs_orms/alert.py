"""File to hold the Alert class and its associated methods."""

from typing import TYPE_CHECKING, Optional

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

    alert_id: str = mapped_column("alert_id", String, primary_key=True)
    cause: Optional[str] = mapped_column("cause", String)
    effect: Optional[str] = mapped_column("effect", String)
    severity: Optional[str] = mapped_column("severity", String)
    stop_id: Optional[str] = mapped_column("stop_id", String)
    agency_id: Optional[str] = mapped_column("agency_id", String)
    route_id: Optional[str] = mapped_column("route_id", String)
    route_type: Optional[str] = mapped_column("route_type", String)
    direction_id: Optional[str] = mapped_column("direction_id", String)
    trip_id: Optional[str] = mapped_column("trip_id", String)
    active_period_end: Optional[int] = mapped_column("active_period_end", Integer)
    header: Optional[str] = mapped_column("header", String)
    description: Optional[str] = mapped_column("description", String)
    url: Optional[str] = mapped_column("url", String)
    active_period_start: Optional[int] = mapped_column("active_period_start", Integer)
    timestamp: Optional[int] = mapped_column("timestamp", Integer)

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
