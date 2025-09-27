"""File to hold the Calendar class and its associated methods."""

import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip


class Transfer(Base):
    """Transfer
    
    denotes that a trip (`from_trip_id`) @ a stop (`from_stop_id`)\
        transfers to another trip (`to_trip_id`) @ another stop (`to_stop_id`)
    
    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#transferstxt
    
    """

    __tablename__ = "transfer"
    __filename__ = "transfers.txt"

    from_stop_id: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("stop.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    to_stop_id: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("stop.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )

    transfer_type: Mapped[t.Optional[str]]
    min_transfer_time: Mapped[t.Optional[int]]
    min_walk_time: Mapped[t.Optional[int]]
    min_wheelchair_time: Mapped[t.Optional[int]]
    suggested_buffer_time: Mapped[t.Optional[int]]
    wheelchair_transfer: Mapped[t.Optional[str]]
    from_trip_id: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("trip.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    to_trip_id: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("trip.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
    )

    index: Mapped[int] = mapped_column(primary_key=True)

    from_stop: Mapped["Stop"] = relationship(
        back_populates="from_stop_transfers", foreign_keys=[from_stop_id]
    )
    to_stop: Mapped["Stop"] = relationship(
        back_populates="to_stop_transfers", foreign_keys=[to_stop_id]
    )
    from_trip: Mapped["Trip"] = relationship(
        back_populates="from_trip_transfers", foreign_keys=[from_trip_id]
    )
    to_trip: Mapped["Trip"] = relationship(
        back_populates="to_trip_transfers", foreign_keys=[to_trip_id]
    )

    to_stop_time: Mapped["StopTime"] = relationship(
        primaryjoin="""and_(
            foreign(Transfer.to_trip_id)==StopTime.trip_id,
            foreign(Transfer.to_stop_id)==StopTime.stop_id
            )""",
        viewonly=True,
    )

    from_stop_time: Mapped["StopTime"] = relationship(
        primaryjoin="""and_(
            foreign(Transfer.from_trip_id)==StopTime.trip_id,
            foreign(Transfer.from_stop_id)==StopTime.stop_id
            )""",
        viewonly=True,
    )

    def __repr__(self) -> str:
        """override for `Base.__repr__`"""
        return f"<{self.__class__}({self.from_trip_id}@{self.from_stop_id} -> {self.to_trip_id}@{self.to_stop_id})>"  # pylint: disable=line-too-long

    def as_label(self) -> str:
        """Returns a label for the transfer, in the format of trip_short_name: trip_headsign"""
        return f"{self.to_trip.trip_short_name}: {self.to_stop_time.destination_label}"
