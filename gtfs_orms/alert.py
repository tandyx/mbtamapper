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

    alert_id: str = mapped_column(String, primary_key=True)
    cause: Optional[str] = mapped_column(String)
    effect: Optional[str] = mapped_column(String)
    severity: Optional[str] = mapped_column(String)
    stop_id: Optional[str] = mapped_column(String)
    agency_id: Optional[str] = mapped_column(String)
    route_id: Optional[str] = mapped_column(String)
    route_type: Optional[str] = mapped_column(String)
    direction_id: Optional[str] = mapped_column(String)
    trip_id: Optional[str] = mapped_column(String)
    active_period_end: Optional[int] = mapped_column(Integer)
    header: Optional[str] = mapped_column(String)
    description: Optional[str] = mapped_column(String)
    url: Optional[str] = mapped_column(String)
    active_period_start: Optional[int] = mapped_column(Integer)
    timestamp: Optional[int] = mapped_column(Integer)

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
