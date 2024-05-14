"""File to hold the MultiRouteTrip class and its associated methods."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .route import Route
    from .trip import Trip


class MultiRouteTrip(Base):  # pylint: disable=too-few-public-methods
    """MultiRotueTrip

    represents added trips

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#multi_route_tripstxt

    """

    __tablename__ = "multi_route_trips"
    __filename__ = "multi_route_trips.txt"

    added_route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )

    trip: Mapped["Trip"] = relationship(back_populates="multi_route_trips")
    route: Mapped["Route"] = relationship(back_populates="multi_route_trips")
