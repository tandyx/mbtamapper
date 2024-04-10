"""File to hold the Prediction class and its associated methods."""

# pylint: disable=line-too-long

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip
    from .vehicle import Vehicle


class Prediction(Base):
    """Prediction"""

    __tablename__ = "predictions"
    __realtime_name__ = "trip_updates"

    prediction_id: Mapped[str]
    arrival_time: Mapped[Optional[int]]
    departure_time: Mapped[Optional[int]]
    direction_id: Mapped[Optional[int]]
    stop_sequence: Mapped[Optional[int]]
    route_id: Mapped[Optional[str]]
    stop_id: Mapped[Optional[str]]
    trip_id: Mapped[Optional[str]]
    vehicle_id: Mapped[Optional[str]]
    index: Mapped[int] = mapped_column(primary_key=True)

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
        self.stop_name = self.stop.stop_name
        self.delay = self._delay

    def __lt__(self, other: "Prediction") -> bool:
        """Implements less than operator.

        Returns:
            - `bool`: whether the object is less than the other
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        return self.stop_sequence < other.stop_sequence

    def __eq__(self, other: "Prediction") -> bool:
        """Implements equality operator.

        Returns:
            - `bool`: whether the objects are equal
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        return self.stop_sequence == other.stop_sequence

    @property
    def _delay(self) -> int:
        """Returns the delay of the prediction.

        Returns:
            - `int`: the delay of the prediction
        """
        if not self.stop_time:
            return 0
        if self.departure_time and self.stop_time.departure_timestamp:
            return self.departure_time - self.stop_time.departure_timestamp
        if self.arrival_time and self.stop_time.arrival_seconds:
            return self.arrival_time - self.stop_time.arrival_timestamp
        return 0

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
