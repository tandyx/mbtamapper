"""File to hold the Calendar class and its associated methods."""
from shapely.geometry import Point
from geojson import Feature

from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy import Column, String, Float, ForeignKey
from gtfs_loader.gtfs_base import GTFSBase


class Stop(GTFSBase):
    """Stop"""

    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True)
    stop_code = Column(String)
    stop_name = Column(String)
    stop_desc = Column(String)
    platform_code = Column(String)
    platform_name = Column(String)
    stop_lat = Column(Float)
    stop_lon = Column(Float)
    zone_id = Column(String)
    stop_address = Column(String)
    stop_url = Column(String)
    level_id = Column(String)
    location_type = Column(String)
    parent_station = Column(String, ForeignKey("stops.stop_id"))
    wheelchair_boarding = Column(String)
    municipality = Column(String)
    on_street = Column(String)
    at_street = Column(String)
    vehicle_type = Column(String)

    stop_times = relationship("StopTime", back_populates="stop", passive_deletes=True)
    parent_stop = relationship(
        "Stop", remote_side=[stop_id], back_populates="child_stops"
    )
    child_stops = relationship("Stop", back_populates="parent_stop")

    predictions = relationship(
        "Prediction",
        back_populates="stop",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    vehicles = relationship(
        "Vehicle",
        back_populates="stop",
        primaryjoin="Stop.stop_id==foreign(Vehicle.stop_id)",
        viewonly=True,
    )
    alerts = relationship(
        "Alert",
        back_populates="stop",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    routes = relationship(
        "Route",
        primaryjoin="Stop.stop_id==StopTime.stop_id",
        secondary="join(StopTime, Trip, StopTime.trip_id==Trip.trip_id)",
        secondaryjoin="Trip.route_id==Route.route_id",
        overlaps="trips,stop_times,route,stop",
    )

    @reconstructor
    def init_on_load(self):
        """Load the parent_stop relationship on load"""
        # pylint: disable=attribute-defined-outside-init

    def __repr__(self):
        return f"<Stop(stop_id={self.stop_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the stop"""
        return Point(self.stop_lat, self.stop_lon)

    def as_dict(self) -> dict:
        """Returns stop object as a dictionary."""
        return {
            "stop_id": self.stop_id,
            "stop_name": self.stop_name,
            "stop_desc": self.stop_desc,
            "platform_code": self.platform_code,
            "platform_name": self.platform_name,
            "zone_id": self.zone_id,
            "stop_address": self.stop_address,
            "stop_url": self.stop_url,
            "level_id": self.level_id,
            "location_type": self.location_type,
            "parent_station": self.parent_station,
            "wheelchair_boarding": self.wheelchair_boarding,
            "municipality": self.municipality,
            "on_street": self.on_street,
            "at_street": self.at_street,
            "vehicle_type": self.vehicle_type,
            "alerts": [alert.as_dict() for alert in self.alerts],
            "predictions": [prediction.as_dict() for prediction in self.predictions],
        }

    def as_feature(self) -> Feature:
        """Returns stop object as a feature.

        Args:
            route_types: A list of route types to include routes for."""

        feature = Feature(
            id=self.stop_id,
            geometry=self.as_point(),
            properties={
                "popupContent": self.as_html_popup(),
                "stop_name": self.stop_name,
            },
        )

        return feature

    def as_html_popup(self) -> str:
        """Returns stop object as an html popup.
        Args:
            route_types: A list of route types to include routes for."""
        routes = []
        for child_stop in self.child_stops:
            if child_stop.location_type != "0":
                continue
            for route in child_stop.routes:
                if route in routes:
                    continue
                routes.append(route)

        routes = sorted(routes, key=lambda x: x.route_type)

        alert = (
            """<img src ="static/alert.png" alt="alert" width=25 height=25 style="margin:2px;">"""
            if self.alerts
            else ""
        )

        wheelchair = (
            """<img src="static/wheelchair.png" alt="accessible" title = "Wheelchair Accessible" width=25 height=25 style="margin:2px;">"""
            if "1" in [s.wheelchair_boarding for s in self.child_stops]
            else ""
        )
        route_colors = ", </a>".join(
            f"<a style='color:#{r.route_color or 'ffffff'};'>{r.route_short_name or r.route_long_name}"
            for r in routes
        )

        html = (
            f"<a href = {self.stop_url} style='color:#{next((r.route_color for r in routes), '008EAA')};font-size:28pt;text-decoration: none;text-align: left'>{self.stop_name}</a></br>"
            f"<body style='color:#ffffff;text-align: left;'>"
            f"{next((s.stop_desc for s in self.child_stops if not s.platform_code), self.child_stops[0].stop_desc if self.child_stops else self.stop_desc)}</br>"
            f"—————————————————————————————————</br>"
            f"{alert} {wheelchair}</br>"
            f"Routes: {route_colors}</a></br>"
            f"Zone: {self.zone_id or ','.join(set(c.zone_id for c in self.child_stops))}</br>"
            f"<a style='color:grey;font-size:9pt'>"
            f"Adress: {self.stop_address}</br>"
            f"Platforms: {', '.join(s.platform_name.strip('Commuter Rail - ') for s in self.child_stops if s.platform_code)}</br>"
            "</a></body>"
        )

        return html
