"""module holding the TripProperty class"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .trip import Trip


class TripProperty(Base):
    """TripProperty

    typically associates with transfers, surprisingly

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#trips_propertiestxt

    """

    __tablename__ = "trip_properties"
    __filename__ = "trips_properties.txt"

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    trip_property_id: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(primary_key=True)

    trip: Mapped["Trip"] = relationship(back_populates="trip_properties")
