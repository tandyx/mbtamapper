"""File to hold the Stop class and its associated methods."""

# pylint: disable=line-too-long
import typing as t

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .alert import Alert
    from .facility import Facility
    from .prediction import Prediction
    from .route import Route
    from .stop_time import StopTime
    from .transfer import Transfer
    from .vehicle import Vehicle


class Stop(Base):
    """Stop

    this table contains the self-referential relationship of stops to parent stops

    `location_type` == 1: parent stop

    Stop(...).parent_stop -> Stop(...).child_stops

    TODO:
        - `Stop(...).get_routes()` is very slow

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#stop_timestxt

    """

    __tablename__ = "stops"
    __filename__ = "stops.txt"

    stop_id: Mapped[str] = mapped_column(primary_key=True)
    stop_code: Mapped[t.Optional[str]]
    stop_name: Mapped[str]
    stop_desc: Mapped[t.Optional[str]]
    platform_code: Mapped[t.Optional[str]]
    platform_name: Mapped[t.Optional[str]]
    stop_lat: Mapped[t.Optional[float]]
    stop_lon: Mapped[t.Optional[float]]
    zone_id: Mapped[t.Optional[str]]
    stop_address: Mapped[t.Optional[str]]
    stop_url: Mapped[t.Optional[str]]
    level_id: Mapped[t.Optional[str]]
    location_type: Mapped[str]  # consider as int?
    parent_station: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("stops.stop_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_boarding: Mapped[str]  # consider as int?
    municipality: Mapped[str]
    on_street: Mapped[t.Optional[str]]
    at_street: Mapped[t.Optional[str]]
    vehicle_type: Mapped[t.Optional[str]]

    stop_times: Mapped[list["StopTime"]] = relationship(
        back_populates="stop", passive_deletes=True
    )
    facilities: Mapped[list["Facility"]] = relationship(
        back_populates="stop", passive_deletes=True
    )
    parent_stop: Mapped["Stop"] = relationship(
        remote_side=[stop_id], back_populates="child_stops"
    )
    child_stops: Mapped[list["Stop"]] = relationship(back_populates="parent_stop")

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="stop",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="stop",
        primaryjoin="Stop.stop_id==foreign(Vehicle.stop_id)",
        viewonly=True,
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="stop",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    routes: Mapped[list["Route"]] = relationship(
        primaryjoin="and_(Stop.stop_id==remote(StopTime.stop_id), StopTime.trip_id==foreign(Trip.trip_id), Trip.route_id==foreign(Route.route_id))",
        viewonly=True,
    )

    to_stop_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="to_stop",
        foreign_keys="Transfer.to_stop_id",
        passive_deletes=True,
    )
    from_stop_transfers: Mapped[list["Transfer"]] = relationship(
        back_populates="from_stop",
        foreign_keys="Transfer.from_stop_id",
        passive_deletes=True,
    )

    # routes: Mapped[list["Route"]] = relationship(
    #     primaryjoin="""or_(
    #         and_(Stop.stop_id==remote(StopTime.stop_id), StopTime.trip_id==foreign(Trip.trip_id), Trip.route_id==foreign(Route.route_id)),
    #         and_(Stop.parent_station==Stop.stop_id, Stop.stop_id==remote(StopTime.stop_id), StopTime.trip_id==foreign(Trip.trip_id), Trip.route_id==foreign(Route.route_id))
    #     )""",
    #     viewonly=True,
    # )

    # all_routes: Mapped[list["Route"]] = relationship(
    #     # remote_side=[stop_id],
    #     foreign_keys=[parent_station],
    #     primaryjoin="Stop.parent_stop",
    #     secondaryjoin="and_(StopTime.trip_id==foreign(Trip.trip_id), Trip.route_id==foreign(Route.route_id))",
    #     secondary="stop_times",
    #     # primaryjoin="and_(Stop.stop_id==remote(StopTime.stop_id), StopTime.trip_id==foreign(Trip.trip_id), Trip.route_id==foreign(Route.route_id))",
    #     viewonly=True,
    # )

    # c_via_secondary = relationship("C", secondary="b",
    #                     primaryjoin="A.b_id == B.id", secondaryjoin="C.id == B.c_id",
    #                     viewonly=True)

    # SELECT DISTINCT parent_stops.*, routes.* FROM stops as parent_stops
    # 	INNER JOIN stops ON parent_stops.stop_id = stops.parent_station
    # 	INNER JOIN stop_times ON stops.stop_id = stop_times.stop_id
    # 	INNER JOIN trips ON stop_times.trip_id = trips.trip_id
    # 	INNER JOIN routes ON trips.route_id = routes.route_id
    # WHERE parent_stops.location_type = 1
    # ORDER BY parent_stops.stop_id;

    @reconstructor
    def _init_on_load_(self):
        """Init on load"""
        self.stop_url = (
            self.stop_url
            or f"https://www.mbta.com/stops/{self.parent_stop.stop_id if self.parent_station else self.stop_id}"
        )

    def as_point(self) -> Point:
        """Returns a shapely Point object of the stop

        returns:
            - `Point`: A shapely Point object of the stop
        """
        return Point(self.stop_lon, self.stop_lat)

    def get_routes(self) -> t.Generator["Route", None, None]:
        """yields a list of routes that stop @ this stop & children

        yields:
            - `Route`: A ***set*** of routes that stop at this stop
        """
        if self.location_type == "1":
            yield from {r for cs in self.child_stops for r in cs.routes}
        else:
            yield from self.routes

    def get_stop_times(self) -> t.Generator["StopTime", None, None]:
        """yields a list of `StopTime` objects for this stop || children

        yields:
            - `StopTime`: stop times for this stop
        """
        if self.location_type == "1":
            yield from (st for cs in self.child_stops for st in cs.stop_times)
        else:
            yield from self.stop_times

    def get_alerts(self) -> t.Generator["Alert", None, None]:
        """yields a list of `Alert` objects for this stop & children

        yields:
            - `Alert`: A set of alerts for this stop
        """
        yield from self.alerts
        yield from (a for cs in self.child_stops for a in cs.alerts)

    def get_predictions(self) -> t.Generator["Prediction", None, None]:
        """yields a list of `Prediction` objects\
            for this stop and its children
        
        yields:
            - `Prediction`: predictions for this stop"""
        if self.location_type == "1":
            yield from (p for cs in self.child_stops for p in cs.predictions)
        else:
            yield from self.predictions

    @t.override
    def as_json(self, *include: str, **kwargs) -> dict[str, t.Any]:
        """returns `Stop(...)` as a json serializable object:

        args:
            - `*include`: other orms/attars to include
            - `*kwargs`: unused \n
        returns:
            - `dict[str, Any]`: json object of stop
        """
        json_dict = super().as_json(*include, **kwargs)
        if "alerts" in include:
            json_dict["alerts"] = [a.as_json() for a in self.get_alerts()]
        if "routes" in include:
            json_dict["routes"] = [r.as_json() for r in self.get_routes()]
        if "stop_times" in include:
            json_dict["stop_times"] = [st.as_json() for st in self.get_stop_times()]
        if "predictions" in include:
            json_dict["predictions"] = [p.as_json() for p in self.get_predictions()]
        return json_dict

    def as_feature(self, *include: str) -> Feature:
        """Returns stop object as a feature.

        Args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: A GeoJSON feature object.
        """
        return Feature(
            id=self.stop_id, geometry=self.as_point(), properties=self.as_json(*include)
        )
