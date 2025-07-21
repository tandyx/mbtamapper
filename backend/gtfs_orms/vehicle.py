"""File to hold the Vehicle class and its associated methods."""

# pylint: disable=line-too-long
import typing as t

from geographiclib.geodesic import Geodesic
from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if t.TYPE_CHECKING:
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

    `source`: https://cdn.mbta.com/realtime/VehiclePositions.pb

    https://github.com/google/transit/blob/master/gtfs-realtime/spec/en/reference.md#message-vehicleposition

    """

    __tablename__ = "vehicles"
    __realtime_name__ = "vehicle_positions"

    vehicle_id: Mapped[str] = mapped_column(primary_key=True)
    trip_id: Mapped[t.Optional[str]]
    route_id: Mapped[t.Optional[str]]
    direction_id: Mapped[t.Optional[int]]
    latitude: Mapped[t.Optional[float]]
    longitude: Mapped[t.Optional[float]]
    bearing: Mapped[t.Optional[float]]
    current_stop_sequence: Mapped[t.Optional[int]]
    current_status: Mapped[t.Optional[str]]
    timestamp: Mapped[t.Optional[int]]
    stop_id: Mapped[t.Optional[str]]
    label: Mapped[t.Optional[str]]
    occupancy_status: Mapped[t.Optional[str]]
    occupancy_percentage: Mapped[t.Optional[int]]
    speed: Mapped[t.Optional[float]]

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
        primaryjoin="""and_(
            foreign(Vehicle.vehicle_id)==Prediction.vehicle_id,
            foreign(Vehicle.stop_id)==Prediction.stop_id,
            foreign(Vehicle.trip_id)==Prediction.trip_id,
        )""",
        viewonly=True,
    )

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.bearing = self.bearing or self.interpolated_bearing or 0
        self.current_stop_sequence = self.current_stop_sequence or 0
        self.trip_short_name = self._trip_short_name()

    def as_point(self) -> Point:
        """Returns vehicle as point.

        returns:
            - `Point`: vehicle as a point
        """
        return Point(self.longitude, self.latitude)

    @t.override
    def as_json(self, *include: str, **kwargs) -> dict[str, t.Any]:
        """Returns vehicle as json.

        args:
            - `*include`: list of strings to include in the json\n
        returns:
            - `dict`: vehicle as a json
        """

        _dict = super().as_json(*include, **kwargs) | {
            "route_color": self.route.route_color if self.route else None,
            "bikes_allowed": self.trip.bikes_allowed == 1 if self.trip else False,
            "speed_mph": self._speed_mph(),
            "headsign": self._headsign(),
            "display_name": self._display_name(),
        }
        # if "trip_properties" in include:
        #     _dict["trip_properties"] = (
        #         [tp.as_json() for tp in self.trip.trip_properties] if self.trip else []
        #     )
        if "to_trip_transfers" in include:
            _dict["to_trip_transfers"] = (
                [tt.as_json() for tt in self.trip.to_trip_transfers]
                if self.trip
                else []
            )
        if "from_trip_transfers" in include:
            _dict["from_trip_transfers"] = (
                [ft.as_json() for ft in self.trip.from_trip_transfers]
                if self.trip
                else []
            )
        return _dict

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

    def get_alerts(self, *orms) -> t.Generator["Alert", None, None]:
        """Returns alerts as json.

        args:
            - `*orms`: list of orms to include in the json\n
        returns:
            - `list`: alerts as json
        """
        # pylint: disable=too-many-nested-blocks
        from .alert import Alert  # pylint: disable=import-outside-toplevel

        for attr in orms:
            orm_list: Base | t.Iterable[Base] | None = getattr(self, attr, None)
            orm_list = [orm_list] if isinstance(orm_list, Base) else orm_list
            if not orm_list:
                continue
            for orm in orm_list:
                for sub_attar_name in dir(orm):
                    if sub_attar_name.startswith("_") or sub_attar_name in self.cols:
                        continue
                    object_attr = getattr(orm, sub_attar_name)
                    if isinstance(object_attr, Alert):
                        yield object_attr
                    if isinstance(object_attr, t.Iterable):
                        for a in object_attr:
                            if isinstance(a, Alert):
                                yield a

    @property
    def interpolated_bearing(self) -> float:
        """interpolates bearing based upon direction, etc wrapper for _get_interpolated bearing"""
        try:
            return self._get_interpolated_bearing()
        except Exception:  # pylint: disable=broad-except
            return self.bearing or 0

    def _get_interpolated_bearing(self) -> float:
        """returns the interpolated bearing"""
        BOSTON_POS = Point(-71.0552, 42.3519)
        shape_line = self.trip.shape.as_linestring()
        shape_line_coords: list[Point] = [Point(pt) for pt in shape_line.coords]
        veh_point: Point = self.as_point()
        nearest, nearest_dist, nearest_i = Point(0, 0), float("inf"), 0
        for i, pt in enumerate(shape_line_coords):
            if pt.distance(veh_point) < nearest_dist:
                nearest, nearest_dist, nearest_i = pt, pt.distance(veh_point), i
        next_pt: Point
        if nearest_i == len(shape_line_coords) - 1:
            next_pt = shape_line_coords[nearest_i - 1]
        elif nearest_i == 0:
            next_pt = shape_line_coords[1]
        # if prev point is further from boston than next
        elif shape_line_coords[nearest_i - 1].distance(BOSTON_POS) > shape_line_coords[
            nearest_i + 1
        ].distance(BOSTON_POS):
            next_pt = (  # outbound, need to find furthest dist from boston
                shape_line_coords[nearest_i - 1]
                if self.direction_id == 0
                else shape_line_coords[nearest_i + 1]
            )
        else:
            next_pt = (
                shape_line_coords[nearest_i + 1]
                if self.direction_id == 0
                else shape_line_coords[nearest_i - 1]
            )
        return Geodesic.WGS84.Inverse(nearest.y, nearest.x, next_pt.y, next_pt.x)[
            "azi1"
        ]

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
            self.route_id  # mypy shit
            and (self.route.route_type == "3" or self.route_id.startswith("Green"))
            and self.route.route_short_name
            and len(self.route.route_short_name) <= 4
        ):
            return self.route.route_short_name
        return ""

    def _headsign(self) -> str:
        """Returns headsign.

        returns:
            - `str`: headsign
        """
        if self.trip:
            return self.trip.trip_headsign
        if self.predictions:
            return max(self.predictions).stop.stop_name
        return "unknown"

    def _trip_short_name(self) -> str | None:
        """Returns trip short name.

        returns:
            - `str`: trip short name
        """

        if self.trip and self.trip.trip_short_name:
            return self.trip.trip_short_name
        return self.trip_id
