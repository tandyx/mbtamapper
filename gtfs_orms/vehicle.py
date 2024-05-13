"""File to hold the Vehicle class and its associated methods."""

# pylint: disable=line-too-long
from typing import TYPE_CHECKING, Any, Generator, Iterable, Optional, override

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .alert import Alert
    from .prediction import Prediction
    from .route import Route
    from .stop import Stop
    from .stop_time import StopTime
    from .trip import Trip


class Vehicle(Base):
    """Vehicle

    very mutated from the original GTFS spec

    this table is realtime and thus violatile. all relationships are viewonly

    """

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
        self.trip_short_name = self._trip_short_name()

    def as_point(self) -> Point:
        """Returns vehicle as point.

        returns:
            - `Point`: vehicle as a point
        """
        return Point(self.longitude, self.latitude)

    @override
    def as_json(self, *include: str, **kwargs) -> dict[str, Any]:
        """Returns vehicle as json.

        args:
            - `*include`: list of strings to include in the json\n
        returns:
            - `dict`: vehicle as a json
        """
        return super().as_json(*include, **kwargs) | {
            "route_color": self.route.route_color if self.route else None,
            "bikes_allowed": self.trip.bikes_allowed == 1 if self.trip else False,
            "speed_mph": self._speed_mph(),
            "headsign": self._headsign(),
            "display_name": self._display_name(),
        }

    @override
    def as_feature(self, *include: str) -> Feature:
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
        # pylint: disable=too-many-nested-blocks
        from .alert import Alert  # pylint: disable=import-outside-toplevel

        for attr in orms:
            orm_list: Base | Iterable[Base] = getattr(self, attr, None)
            orm_list = [orm_list] if isinstance(orm_list, Base) else orm_list
            for orm in orm_list:
                for sub_attar_name in dir(orm):
                    if sub_attar_name.startswith("_") or sub_attar_name in self.cols:
                        continue
                    object_attr = getattr(orm, sub_attar_name)
                    if isinstance(object_attr, Alert):
                        yield object_attr
                    if isinstance(object_attr, Iterable):
                        for a in object_attr:
                            if isinstance(a, Alert):
                                yield a

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

    def _headsign(self) -> str:
        """Returns headsign.

        returns:
            - `str`: headsign
        """

        # self.trip.trip_headsign if self.trip else max(self.predictions, key=lambda x: x.stop_sequence).stop.stop_name if self.predictions else "Unknown"

        if self.trip:
            return self.trip.trip_headsign
        if self.predictions:
            return max(self.predictions).stop.stop_name
        return "unknown"

    def _trip_short_name(self) -> str:
        """Returns trip short name.

        returns:
            - `str`: trip short name
        """

        if self.trip and self.trip.trip_short_name:
            return self.trip.trip_short_name
        return self.trip_id
