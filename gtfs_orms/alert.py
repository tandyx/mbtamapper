"""File to hold the Alert class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .trip import Trip


class Alert(Base):
    """Alerts"""

    __tablename__ = "alerts"
    __realtime_name__ = "service_alerts"

    alert_id: Mapped[str] = mapped_column(primary_key=True)
    cause: Mapped[Optional[str]]
    effect: Mapped[Optional[str]]
    severity: Mapped[Optional[str]]
    stop_id: Mapped[Optional[str]]
    agency_id: Mapped[Optional[str]]
    route_id: Mapped[Optional[str]]
    route_type: Mapped[Optional[str]]
    direction_id: Mapped[Optional[str]]
    trip_id: Mapped[Optional[str]]
    active_period_end: Mapped[Optional[int]]
    header: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    active_period_start: Mapped[Optional[int]]
    timestamp: Mapped[Optional[int]]

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

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
