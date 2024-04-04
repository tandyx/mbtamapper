"""File to hold the Prediction class and its associated methods."""

# pylint: disable=line-too-long

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"
    __realtime_name__ = "trip_updates"

    prediction_id: str = mapped_column(String, primary_key=True)
    arrival_time: Optional[str] = mapped_column(String)
    departure_time: Optional[str] = mapped_column(String)
    direction_id: Optional[str] = mapped_column(String)
    stop_sequence: Optional[int] = mapped_column(Integer)
    route_id: Optional[str] = mapped_column(String)
    stop_id: Optional[str] = mapped_column(String)
    trip_id: Optional[str] = mapped_column(String)
    vehicle_id: Optional[str] = mapped_column(String)

    route = relationship(
        "Route",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    vehicle = relationship(
        "Vehicle",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.vehicle_id)==Vehicle.vehicle_id",
        viewonly=True,
    )

    stop_time = relationship(
        "StopTime",
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
