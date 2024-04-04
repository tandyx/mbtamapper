"""File to hold the Stop class and its associated methods."""

# pylint: disable=line-too-long
from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

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

    stop_id: Optional[str] = mapped_column(String, primary_key=True)
    stop_code: Optional[str] = mapped_column(String)
    stop_name: Optional[str] = mapped_column(String)
    stop_desc: Optional[str] = mapped_column(String)
    platform_code: Optional[str] = mapped_column(String)
    platform_name: Optional[str] = mapped_column(String)
    stop_lat: Optional[float] = mapped_column(Float)
    stop_lon: Optional[float] = mapped_column(Float)
    zone_id: Optional[str] = mapped_column(String)
    stop_address: Optional[str] = mapped_column(String)
    stop_url: Optional[str] = mapped_column(String)
    level_id: Optional[str] = mapped_column(String)
    location_type: Optional[str] = mapped_column(String)
    parent_station: Optional[str] = mapped_column(
        String, ForeignKey("stops.stop_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_boarding: Optional[str] = mapped_column(String)
    municipality: Optional[str] = mapped_column(String)
    on_street: Optional[str] = mapped_column(String)
    at_street: Optional[str] = mapped_column(String)
    vehicle_type: Optional[str] = mapped_column(String)

    stop_times: list["StopTime"] = relationship(
        "StopTime", back_populates="stop", passive_deletes=True
    )
    facilities: list["Facility"] = relationship(
        "Facility", back_populates="stop", passive_deletes=True
    )
    parent_stop: Optional["Stop"] = relationship(
        "Stop", remote_side=[stop_id], back_populates="child_stops"
    )
    child_stops: list["Stop"] = relationship("Stop", back_populates="parent_stop")

    predictions: list["Prediction"] = relationship(
        "Prediction",
        back_populates="stop",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    vehicles: list["Vehicle"] = relationship(
        "Vehicle",
        back_populates="stop",
        primaryjoin="Stop.stop_id==foreign(Vehicle.stop_id)",
        viewonly=True,
    )
    alerts: list["Alert"] = relationship(
        "Alert",
        back_populates="stop",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    routes: list["Route"] = relationship(
        "Route",
        primaryjoin="Stop.stop_id==StopTime.stop_id",
        secondary="join(StopTime, Trip, StopTime.trip_id==Trip.trip_id)",
        secondaryjoin="Trip.route_id==Route.route_id",
        overlaps="trips,stop_times,route,stop",
    )

    @reconstructor
    def _init_on_load_(self):
        """Init on load"""
        self.stop_url = (
            self.stop_url
            or f"https://www.mbta.com/stops/{self.parent_stop.stop_id if self.parent_station else self.stop_id}"
        )

    def as_point(self) -> Point:
        """Returns a shapely Point object of the stop"""
        return Point(self.stop_lon, self.stop_lat)

    def return_routes(self) -> set:
        """Returns a list of routes that stop at this stop"""
        return sorted(
            {
                r
                for cs in (cs for cs in self.child_stops if cs.location_type == "0")
                for r in cs.routes
            },
            key=lambda x: x.route_type,
        )

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
