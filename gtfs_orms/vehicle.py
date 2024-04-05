"""File to hold the Vehicle class and its associated methods."""

# pylint: disable=line-too-long
from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import mapped_column, reconstructor, relationship, Mapped

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

    vehicle_id: Mapped[str] = mapped_column(primary_key=True)
    trip_id: Mapped[Optional[str]]
    route_id: Mapped[Optional[str]]
    direction_id: Mapped[Optional[str]]
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    bearing: Mapped[Optional[float]]
    current_stop_sequence: Mapped[Optional[int]]
    current_status: Mapped[Optional[str]]
    timestamp: Mapped[Optional[int]]
    stop_id: Mapped[Optional[str]]
    label: Mapped[Optional[str]]
    occupancy_status: Mapped[Optional[str]]
    occupancy_percentage: Mapped[Optional[int]]
    speed: Mapped[Optional[float]]

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="vehicle",
        primaryjoin="Vehicle.trip_id==foreign(Prediction.trip_id)",
        viewonly=True,
    )
    route: Mapped["Route"] = relationship(
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    stop: Mapped["Stop"] = relationship(
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip: Mapped["Trip"] = relationship(
        back_populates="vehicle",
        primaryjoin="foreign(Vehicle.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    next_stop: Mapped[list["Prediction"]] = relationship(
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
        self.route_color = self.route.route_color if self.route else None
        self.bikes_allowed = self.trip.bikes_allowed == 1 if self.trip else False
        self.display_name = (
            self.trip.trip_short_name
            if self.trip and self.trip.trip_short_name
            else (
                self.route.route_short_name
                if self.route
                and (self.route.route_type == "3" or self.route_id.startswith("Green"))
                and self.route.route_short_name
                else ""
            )
        )

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
