"""File to hold the StopTime class and its associated methods."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from helper_functions import *

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .stop import Stop
    from .trip import Trip


class StopTime(GTFSBase):
    """Stop Times"""

    __tablename__ = "stop_times"
    __filename__ = "stop_times.txt"

    trip_id: str = mapped_column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    arrival_time: Optional[str] = mapped_column(String)
    departure_time: Optional[str] = mapped_column(String)
    stop_id: Optional[str] = mapped_column(
        String, ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    stop_sequence: Optional[int] = mapped_column(Integer, primary_key=True)
    stop_headsign: Optional[str] = mapped_column(String)
    pickup_type: Optional[str] = mapped_column(String)
    drop_off_type: Optional[str] = mapped_column(String)
    timepoint: Optional[str] = mapped_column(String)
    checkpoint_id: Optional[str] = mapped_column(String)
    continuous_pickup: Optional[str] = mapped_column(String)
    continuous_drop_off: Optional[str] = mapped_column(String)

    stop: "Stop" = relationship("Stop", back_populates="stop_times")
    trip: "Trip" = relationship("Trip", back_populates="stop_times")

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database.
        executes after the object is loaded from the database and in init"""
        # pylint: disable=attribute-defined-outside-init
        self.destination_label = self.stop_headsign or self.trip.trip_headsign
        self.departure_seconds = to_seconds(self.departure_time)
        self.arrival_seconds = to_seconds(self.arrival_time)
        self.unix_departure_time = self.departure_seconds + get_date().timestamp()
        self.unix_arrival_time = self.arrival_seconds + get_date().timestamp()

    def is_flag_stop(self) -> bool:
        """Returns true if this StopTime is a flag stop"""
        return self.trip.route.route_type == "2" and (
            self.pickup_type == "3" or self.drop_off_type == "3"
        )

    def is_early_departure(self) -> bool:
        """Returns true if this StopTime is an early departure stop"""
        return (
            self.trip.route.route_type == "2"
            and self.timepoint == "0"
            and not self.is_destination()
        )

    def is_active(self, date: datetime) -> bool:
        """Returns true if this StopTime is active on the given date and time"""

        return self.trip.calendar.operates_on_date(date) and self.departure_seconds > (
            get_current_time().timestamp() - get_date().timestamp()
        )

    def is_destination(self) -> bool:
        """Returns true if this StopTime is the last stop in the trip"""
        return self.stop_sequence == max(
            st.stop_sequence for st in self.trip.stop_times
        )
