"""File to hold the Stop class and its associated methods."""

# pylint: disable=line-too-long
import time
from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .alert import Alert
    from .facility import Facility
    from .prediction import Prediction
    from .route import Route
    from .stop_time import StopTime
    from .vehicle import Vehicle


class Stop(GTFSBase):
    """Stop"""

    __tablename__ = "stops"
    __filename__ = "stops.txt"

    stop_id: Mapped[Optional[str]] = mapped_column(primary_key=True)
    stop_code: Mapped[Optional[str]]
    stop_name: Mapped[Optional[str]]
    stop_desc: Mapped[Optional[str]]
    platform_code: Mapped[Optional[str]]
    platform_name: Mapped[Optional[str]]
    stop_lat: Mapped[Optional[float]]
    stop_lon: Mapped[Optional[float]]
    zone_id: Mapped[Optional[str]]
    stop_address: Mapped[Optional[str]]
    stop_url: Mapped[Optional[str]]
    level_id: Mapped[Optional[str]]
    location_type: Mapped[Optional[str]]
    parent_station: Mapped[Optional[str]] = mapped_column(
        ForeignKey("stops.stop_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_boarding: Mapped[Optional[str]]
    municipality: Mapped[Optional[str]]
    on_street: Mapped[Optional[str]]
    at_street: Mapped[Optional[str]]
    vehicle_type: Mapped[Optional[str]]

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

    # all_routes: Mapped[list["Route"]] = relationship(
    #     # remote_side=[stop_id],
    #     # foreign_keys=[parent_station],
    #     primaryjoin="and_(Stop.stop_id==remote(StopTime.stop_id), Stop.stop_id==remote(Stop.parent_station))",
    #     secondary="stop_times",
    #     secondaryjoin="and_(StopTime.trip_id==Trip.trip_id, Trip.route_id==Route.route_id)",
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

    def get_routes(self) -> set["Route"]:
        """Returns a list of routes that stop at this stop

        returns:
            - `set[Route]`: A set of routes that stop at this stop
        """
        if self.location_type == "1":
            routes = {r for cs in self.child_stops for r in cs.routes}
        else:
            routes = set(self.routes)
        return routes

    def as_feature(self, *include: str) -> Feature:
        """Returns stop object as a feature.

        Args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: A GeoJSON feature object.
        """
        # routes = self.all_routes
        properties = self.as_json(*include)
        properties |= {
            "routes": [r.as_json() for r in self.get_routes()],
            "timestamp": time.time(),
        }
        return Feature(id=self.stop_id, geometry=self.as_point(), properties=properties)
