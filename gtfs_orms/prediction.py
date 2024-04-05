"""File to hold the Prediction class and its associated methods."""

# pylint: disable=line-too-long

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip
    from .vehicle import Vehicle


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"
    __realtime_name__ = "trip_updates"

    prediction_id: Mapped[str] = mapped_column(primary_key=True)
    arrival_time: Mapped[Optional[int]]
    departure_time: Mapped[Optional[int]]
    direction_id: Mapped[Optional[str]]
    stop_sequence: Mapped[Optional[int]]
    route_id: Mapped[Optional[str]]
    stop_id: Mapped[Optional[str]]
    trip_id: Mapped[Optional[str]]
    vehicle_id: Mapped[Optional[str]]

    route: Mapped["Route"] = relationship(
        back_populates="predictions",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    stop: Mapped["Stop"] = relationship(
        back_populates="predictions",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip: Mapped["Trip"] = relationship(
        back_populates="predictions",
        primaryjoin="foreign(Prediction.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="predictions",
        primaryjoin="foreign(Prediction.vehicle_id)==Vehicle.vehicle_id",
        viewonly=True,
    )

    stop_time: Mapped["StopTime"] = relationship(
        primaryjoin="""and_(foreign(Prediction.trip_id)==StopTime.trip_id,
                            foreign(Prediction.stop_id)==StopTime.stop_id,)""",
        viewonly=True,
        uselist=False,
    )

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts arrival_time and departure_time to datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        self.stop_sequence = self.stop_sequence or 0
