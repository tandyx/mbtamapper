"""File to hold the MultiRouteTrip class and its associated methods."""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from ..base import GTFSBase


class MultiRouteTrip(GTFSBase):
    """Multi Route Trip"""

    __tablename__ = "multi_route_trips"
    __filename__ = "multi_route_trips.txt"

    added_route_id = Column(
        String,
        ForeignKey("routes.route_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    trip_id = Column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    trip = relationship("Trip", back_populates="multi_route_trips")
    route = relationship("Route", back_populates="multi_route_trips")

    def __repr__(self) -> str:
        return f"<MultiRouteTrip(added_route_id={self.added_route_id}, trip_id={self.trip_id})>"
