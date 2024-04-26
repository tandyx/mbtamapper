"""File to hold the StopTime class and its associated methods."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from helper_functions import *

from .base import Base

if TYPE_CHECKING:
    from .prediction import Prediction
    from .stop import Stop
    from .trip import Trip


class StopTime(Base):
    """Stop Times"""

    __tablename__ = "stop_times"
    __filename__ = "stop_times.txt"

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    arrival_time: Mapped[Optional[str]]
    departure_time: Mapped[Optional[str]]
    stop_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    stop_sequence: Mapped[Optional[int]] = mapped_column(primary_key=True)
    stop_headsign: Mapped[Optional[str]]
    pickup_type: Mapped[Optional[str]]
    drop_off_type: Mapped[Optional[str]]
    timepoint: Mapped[Optional[str]]
    checkpoint_id: Mapped[Optional[str]]
    continuous_pickup: Mapped[Optional[str]]
    continuous_drop_off: Mapped[Optional[str]]

    stop: Mapped["Stop"] = relationship(back_populates="stop_times")
    trip: Mapped["Trip"] = relationship(back_populates="stop_times")
    prediction: Mapped["Prediction"] = relationship(
        primaryjoin="""and_(
            foreign(StopTime.trip_id)==Prediction.trip_id, 
            foreign(StopTime.stop_sequence)==Prediction.stop_sequence
        )""",
        uselist=False,
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database.
        executes after the object is loaded from the database and in init"""
        # pylint: disable=attribute-defined-outside-init
        self.destination_label = self.stop_headsign or self.trip.trip_headsign
        self.departure_seconds = to_seconds(self.departure_time)
        self.arrival_seconds = to_seconds(self.arrival_time)
        self.departure_timestamp = self.departure_seconds + get_date().timestamp()
        self.arrival_timestamp = self.arrival_seconds + get_date().timestamp()
        self.stop_name = self.stop.stop_name

    def __lt__(self, other: "StopTime") -> bool:
        """Implements less than operator.

        Returns:
            - `bool`: whether the object is less than the other
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        return self.stop_sequence < other.stop_sequence

    def __eq__(self, other: "StopTime") -> bool:
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
    def is_flag_stop(self) -> bool:
        """Returns true if this StopTime is a flag stop

        returns:
            - `bool`: whether the stop is a flag stop
        """
        return self.trip.route.route_type == "2" and (
            self.pickup_type == "3" or self.drop_off_type == "3"
        )

    @property
    def is_early_departure(self) -> bool:
        """Returns true if this StopTime is an early departure stop

        returns:
            - `bool`: whether the stop is an early departure stop
        """
        return (
            self.trip.route.route_type == "2"
            and self.timepoint == "0"
            and not self.is_destination()
        )

    def is_active(self, date: datetime) -> bool:
        """Returns true if this StopTime is active on the given date and time

        returns:
            - `bool`: whether the stop is active on the given date and time
        """
        return self.trip.calendar.operates_on(date) and self.departure_seconds > (
            get_current_time().timestamp() - get_date().timestamp()
        )

    @property
    def is_destination(self) -> bool:
        """Returns true if this StopTime is the last stop in the trip

        returns:
            - `bool`: whether the stop is the last stop in the trip
        """
        return self.stop_sequence == max(
            st.stop_sequence for st in self.trip.stop_times
        )

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
