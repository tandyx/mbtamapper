"""File to hold the Vehicle class and its associated methods."""

# pylint: disable=line-too-long
from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .prediction import Prediction
    from .route import Route
    from .stop import Stop
    from .trip import Trip


class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"
    __realtime_name__ = "vehicle_positions"

    vehicle_id: str = mapped_column(String, primary_key=True)
    trip_id: Optional[str] = mapped_column(String)
    route_id: Optional[str] = mapped_column(String)
    direction_id: Optional[str] = mapped_column(String)
    latitude: Optional[float] = mapped_column(Float)
    longitude: Optional[float] = mapped_column(Float)
    bearing: Optional[float] = mapped_column(Float)
    current_stop_sequence: Optional[int] = mapped_column(Integer)
    current_status: Optional[str] = mapped_column(String)
    timestamp: Optional[int] = mapped_column(Integer)
    stop_id: Optional[str] = mapped_column(String)
    label: Optional[str] = mapped_column(String)
    occupancy_status: Optional[str] = mapped_column(String)
    occupancy_percentage: Optional[int] = mapped_column(Integer)
    speed: Optional[float] = mapped_column(Float)

    predictions: list["Prediction"] = relationship(
        "Prediction",
        back_populates="vehicle",
        primaryjoin="Vehicle.trip_id==foreign(Prediction.trip_id)",
        viewonly=True,
    )
    route: "Route" = relationship(
        "Route",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    stop: "Stop" = relationship(
        "Stop",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip: "Trip" = relationship(
        "Trip",
        back_populates="vehicle",
        primaryjoin="foreign(Vehicle.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    next_stop_prediction: list["Prediction"] = relationship(
        "Prediction",
        primaryjoin="""and_(foreign(Vehicle.vehicle_id)==Prediction.vehicle_id,
                            foreign(Vehicle.stop_id)==Prediction.stop_id)""",
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.bearing = self.bearing or 0
        self.current_stop_sequence = self.current_stop_sequence or 0
        self.speed = self.speed if not self.speed else self.speed * 2.23694

    def as_point(self) -> Point:
        """Returns vehicle as point."""
        return Point(self.longitude, self.latitude)

    def as_feature(self, *include) -> Feature:
        """Returns vehicle as feature.

        args:
            - `*include`: list of strings to include in the feature\n
        returns:
            - `Feature`: vehicle as a geojson feature
        """

        return Feature(
            id=self.vehicle_id,
            geometry=self.as_point(),
            properties=self.as_json(*include),
        )
