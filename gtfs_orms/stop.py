"""File to hold the Stop class and its associated methods."""

# pylint: disable=line-too-long
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
