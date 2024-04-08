"""File to hold the Vehicle class and its associated methods."""

# pylint: disable=line-too-long
from typing import TYPE_CHECKING, Generator, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .alert import Alert
    from .prediction import Prediction
    from .route import Route
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip


class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"
    __realtime_name__ = "vehicle_positions"

    vehicle_id: Mapped[str] = mapped_column(primary_key=True)
    trip_id: Mapped[Optional[str]]
    route_id: Mapped[Optional[str]]
    direction_id: Mapped[Optional[int]]
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

    stop_time: Mapped["StopTime"] = relationship(
        primaryjoin="""and_(foreign(Vehicle.trip_id)==StopTime.trip_id,
                            foreign(Vehicle.stop_id)==StopTime.stop_id,)""",
        viewonly=True,
        uselist=False,
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
        self.route_color = self.route.route_color if self.route else None
        self.bikes_allowed = self.trip.bikes_allowed == 1 if self.trip else False
        self.speed_mph = self._speed_mph
        self.trip_short_name = self._trip_short_name
        self.headsign = self._headsign
        self.wheelchair_accessible = self._wheelchair_accessible
        self.display_name = self._display_name

    def as_point(self) -> Point:
        """Returns vehicle as point.

        returns:
            - `Point`: vehicle as a point
        """
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

    def get_alerts(self, *orms) -> Generator["Alert", None, None]:
        """Returns alerts as json.

        args:
            - `*orms`: list of orms to include in the json\n
        returns:
            - `list`: alerts as json
        """

        for attr in orms:
            _alerts = getattr(self, attr, None)
            if not _alerts:
                continue
            for al in getattr(_alerts, "alerts", []):
                yield al

    @property
    def _speed_mph(self) -> float | None:
        """Returns speed.

        returns:
            - `float`: speed
        """
        if not self.speed and self.current_status == "STOPPED_AT":
            return 0
        if not self.speed:
            return self.speed
        return self.speed * 2.23694

    @property
    def _display_name(self) -> str:
        """Returns display name.

        returns:
            - `str`: display name
        """

        if self.trip and self.trip.trip_short_name:
            return self.trip.trip_short_name
        if (
            self.route
            and (self.route.route_type == "3" or self.route_id.startswith("Green"))
            and self.route.route_short_name
        ):
            return self.route.route_short_name
        return ""

    @property
    def _wheelchair_accessible(self) -> bool:
        """Returns wheelchair accessible.

        returns:
            - `bool`: wheelchair accessible
        """
        if self.trip:
            return bool(self.trip.wheelchair_accessible)
        return any(x.stop.wheelchair_boarding for x in self.predictions)

    @property
    def _headsign(self) -> str:
        """Returns headsign.

        returns:
            - `str`: headsign
        """

        if self.trip:
            return self.trip.trip_headsign
        if self.predictions:
            return max(self.predictions).stop.stop_name
        return ""

    @property
    def _trip_short_name(self) -> str:
        """Returns trip short name.

        returns:
            - `str`: trip short name
        """

        if self.trip and self.trip.trip_short_name:
            return self.trip.trip_short_name
        return self.trip_id
