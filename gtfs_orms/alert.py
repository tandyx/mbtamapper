"""File to hold the Alert class and its associated methods."""

import typing as t

from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .trip import Trip


class Alert(Base):
    """Alert

    realtime class for the `service_alerts` feed.

    `source`: https://cdn.mbta.com/realtime/Alerts.pb

    https://github.com/google/transit/blob/master/gtfs-realtime/spec/en/reference.md#message-alert

    """

    __tablename__ = "alerts"
    __realtime_name__ = "service_alerts"

    alert_id: Mapped[str] = mapped_column(primary_key=True)
    cause: Mapped[t.Optional[str]]
    effect: Mapped[t.Optional[str]]
    severity: Mapped[t.Optional[str]]
    stop_id: Mapped[t.Optional[str]]
    agency_id: Mapped[t.Optional[str]]
    route_id: Mapped[t.Optional[str]]
    route_type: Mapped[t.Optional[str]]
    direction_id: Mapped[t.Optional[str]]
    trip_id: Mapped[t.Optional[str]]
    active_period_end: Mapped[t.Optional[int]]
    header: Mapped[t.Optional[str]]
    description: Mapped[t.Optional[str]]
    url: Mapped[t.Optional[str]]
    active_period_start: Mapped[t.Optional[int]]
    timestamp: Mapped[t.Optional[int]]

    route: Mapped["Route"] = relationship(
        back_populates="alerts",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )
    trip: Mapped["Trip"] = relationship(
        back_populates="alerts",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    stop: Mapped["Stop"] = relationship(
        back_populates="alerts",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self):
        """Loads active_period_end and active_period_start as datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        self.url = self.url or "https://www.mbta.com/"
