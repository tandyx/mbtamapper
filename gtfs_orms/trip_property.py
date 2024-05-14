"""module holding the TripProperty class"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .trip import Trip


class TripProperty(Base):
    """TripProperty

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#trips_propertiestxt

    """

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    trip_property_id: Mapped[str] = mapped_column(primary_key=True)
    property_value: Mapped[Optional[str]]

    trip = Mapped["Trip"] = relationship(back_populates="trip_properties")
