"""File to hold the StopTime class and its associated methods."""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import datetime as dt
import time
import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from ..helper_functions import get_date, to_seconds
from .base import Base

if t.TYPE_CHECKING:
    from .prediction import Prediction
    from .stop import Stop
    from .transfer import Transfer
    from .trip import Trip


class StopTime(Base):
    """Stop Times

    this can also be called a tripstop in keolis terms

    represents one trip @ one stop

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#stop_timestxt

    """

    __tablename__ = "stop_times"
    __filename__ = "stop_times.txt"

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    arrival_time: Mapped[str]
    departure_time: Mapped[str]
    stop_id: Mapped[str] = mapped_column(
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    stop_sequence: Mapped[int] = mapped_column(primary_key=True)
    stop_headsign: Mapped[t.Optional[str]]
    pickup_type: Mapped[str]  # consider as int?
    drop_off_type: Mapped[str]  # consider as int?
    timepoint: Mapped[t.Optional[str]]  # consider as int?
    checkpoint_id: Mapped[t.Optional[str]]
    continuous_pickup: Mapped[t.Optional[str]]
    continuous_drop_off: Mapped[t.Optional[str]]

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
    to_transfer: Mapped["Transfer"] = relationship(
        "Transfer",
        primaryjoin="""and_(
            StopTime.trip_id==foreign(Transfer.to_trip_id),
            StopTime.stop_id==foreign(Transfer.to_stop_id) 
            )""",
        viewonly=True,
    )

    from_transfer: Mapped["Transfer"] = relationship(
        "Transfer",
        primaryjoin="""and_(
            StopTime.trip_id==foreign(Transfer.from_trip_id),
            StopTime.stop_id==foreign(Transfer.from_stop_id)
            )""",
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database.
        executes after the object is loaded from the database and in init"""
        # pylint: disable=attribute-defined-outside-init
        _unix_time = get_date().timestamp()
        self.destination_label = self.stop_headsign or self.trip.trip_headsign
        self.departure_timestamp = to_seconds(self.departure_time) + _unix_time
        self.arrival_timestamp = to_seconds(self.arrival_time) + _unix_time
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

        if not self.trip_id == other.trip_id:
            return super().__lt__(other)
        return self.stop_sequence < other.stop_sequence

    def is_flag_stop(self) -> bool:
        """Returns true if this StopTime is a flag stop

        returns:
            - `bool`: whether the stop is a flag stop
        """
        return self.trip.route.route_type == "2" and (
            self.pickup_type == "3" or self.drop_off_type == "3"
        )

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

    def is_active(self, _date: dt.datetime | None = None, **kwargs) -> bool:
        """Returns true if this StopTime is active on the given date and time

        args:
            - `date (datetime = None)`: the date to check <- defaults to the current date
            - `kwargs`: additional arguments passed to `get_date` \n
        returns:
            - `bool`: whether the stop is active on the given date and time
        """

        _date = _date or get_date(**kwargs)

        return (
            self.trip.calendar.operates_on(_date)
            and self.departure_timestamp > time.time()
        ) or bool(self.prediction)

    @property
    def active(self) -> bool:
        """wrapper for self.is_active"""
        return self.is_active(get_date())

    def is_destination(self) -> bool:
        """Returns true if this StopTime is the last stop in the trip

        returns:
            - `bool`: whether the stop is the last stop in the trip
        """
        return self.stop == self.trip.destination

    @t.override
    def _as_json_dict(self) -> dict[str, t.Any]:
        """Returns a dict representation of the object

        returns:
            - `dict`: the object as a dictionary
        """
        return super()._as_json_dict() | {
            "flag_stop": self.is_flag_stop(),
            "early_departure": self.is_early_departure(),
        }
