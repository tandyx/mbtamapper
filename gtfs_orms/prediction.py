"""File to hold the Prediction class and its associated methods."""

# pylint: disable=line-too-long

from typing import TYPE_CHECKING, Any, Optional, Union, override

from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .route import Route
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip
    from .vehicle import Vehicle


class Prediction(Base):
    """Prediction

    mutated from the original GTFS spec

    this table is realtime and thus violatile. all relationships are viewonly

    this is better known as a TripUpdate,\
        but i called it prediction way back then and never changed it :P
    
    https://github.com/google/transit/blob/master/gtfs-realtime/spec/en/reference.md#message-tripupdate

    """

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

    @property
    def destination(self) -> Union["Stop", None]:
        """Returns the destination of the prediction.

        Returns:
            - `str`: the destination of the prediction
        """
        if self.trip:
            return self.trip.destination
        try:
            return max(s for s in self.vehicle.predictions if s.trip_id == self.trip_id)
        except ValueError:
            return None

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts arrival_time and departure_time to datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        self.stop_sequence = self.stop_sequence or 0
        self.stop_name = self.stop.stop_name if self.stop else None
        self.delay = self._get_delay()

    def __repr__(self) -> str:
        """override for `Base.__repr__`"""

        return (
            f"<{self.__class__}({self.trip_id}, {self.stop_id}, {self.stop_sequence})>"
        )

    def __lt__(self, other: "Prediction") -> bool:
        """Implements less than operator.

        Returns:
            - `bool`: whether the object is less than the other
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        if self.trip_id == other.trip_id:
            return self.stop_sequence < other.stop_sequence
        return super().__lt__(other)

    def __eq__(self, other: "Prediction") -> bool:
        """Implements equality operator.

        Returns:
            - `bool`: whether the objects are equal
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )

        if self.trip_id == other.trip_id:
            return self.stop_sequence == other.stop_sequence
        return super().__eq__(other)

    def _get_delay(self) -> int | float | None:
        """Returns the delay of the prediction.

        Returns:
            - `int`: the delay of the prediction
        """
        if not self.stop_time:
            return None
        if self.departure_time and self.stop_time.departure_timestamp:
            delay = self.departure_time - self.stop_time.departure_timestamp
        elif self.arrival_time and self.stop_time.arrival_timestamp:
            delay = self.arrival_time - self.stop_time.arrival_timestamp
        else:
            delay = 0
        if delay <= -60_000:
            delay += 86_400
        return delay

    def get_headsign(self) -> str:
        """Returns the headsign of the prediction.

        Returns:
            - `str`: the headsign of the prediction
        """
        if self.stop_time:
            return self.stop_time.destination_label
        if self.vehicle and self.vehicle.predictions:
            return max(self.vehicle.predictions).stop.stop_name
        return ""

    @override
    def as_json(self, *include: str, **kwargs) -> dict[str, Any]:
        """returns `Prediction` as a dictionary.\
            overrides `as_json` in `Base`.
        
        args:
            - `*include`: A list of properties to include in the dictionary.
            - `**kwargs`: unused\n
        Returns:
            - `dict[str, Any]`: `Prediction` as a dictionary.
        """
        return super().as_json(*include, **kwargs) | {"headsign": self.get_headsign()}
