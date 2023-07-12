"""Vehicle"""
from datetime import datetime
import pytz
from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor

from shapely.geometry import Point
from geojson import Feature

from gtfs_loader.gtfs_base import GTFSBase


class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"

    vehicle_id = Column(String, primary_key=True)
    vehicle_type = Column(String)
    bearing = Column(Float)
    current_status = Column(String)
    current_stop_sequence = Column(Integer)
    direction_id = Column(String)
    label = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    occupancy_status = Column(String)
    speed = Column(Float)
    updated_at = Column(String)
    links_self = Column(String)
    route_id = Column(String)
    stop_id = Column(String)
    trip_id = Column(String)

    predictions = relationship(
        "Prediction",
        back_populates="vehicle",
        primaryjoin="Vehicle.vehicle_id==foreign(Prediction.vehicle_id)",
        viewonly=True,
    )
    route = relationship(
        "Route",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="vehicles",
        primaryjoin="foreign(Vehicle.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="vehicle",
        primaryjoin="foreign(Vehicle.trip_id)==Trip.trip_id",
        viewonly=True,
    )

    next_stop_prediction = relationship(
        "Prediction",
        primaryjoin="""and_(foreign(Vehicle.vehicle_id)==Prediction.vehicle_id,
                            foreign(Vehicle.stop_id)==Prediction.stop_id)""",
        viewonly=True,
    )

    DATETIME_MAPPER = {"updated_at": "updated_at_datetime"}

    DIRECTION_MAPPER = {"0": "Outbound", "1": "Inbound"}

    @reconstructor
    def init_on_load(self):
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.updated_at_datetime = isoparse(self.updated_at)

    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id})>"

    def return_current_status(self) -> str:
        """Returns current status of vehicle."""
        current_status = (
            f"""Vehicle {self.label or self.vehicle_id} """
            f"""{self.current_status.lower().replace("_", " ")} """
            f"""<a href={self.stop.stop_url}>{self.stop.stop_name}</a> - {self.stop.platform_name if self.stop.platform_code else ''} """
            f"""{self.next_stop_prediction.status_as_string() if self.next_stop_prediction else '(Delay Unknown)'}"""
        )

        return current_status

    def as_point(self) -> Point:
        """Returns vehicle as point."""
        return Point(self.latitude, self.longitude)

    def as_dict(self) -> dict[str]:
        """Returns vehicle as dict."""

        return {
            "label": self.label or self.vehicle_id,
            "trip": self.trip.trip_short_name or self.trip.trip_headsign,
            "direction": self.DIRECTION_MAPPER.get(self.direction_id, "Unknown"),
            "vehicle_type": self.vehicle_type,
            "bearing": self.bearing,
            "current_status": self.return_current_status(),
            "current_stop_sequence": self.current_stop_sequence,
            "direction_id": self.direction_id,
            "occupancy_status": self.occupancy_status,
            "speed": self.speed,
            "updated_at": self.updated_at_datetime.strftime("%m/%d/%Y %I:%M%p"),
            "alerts": [a.as_dict() for a in self.trip.alerts],
            "predictions": [prediction.as_dict() for prediction in self.predictions],
        }

    def as_feature(self) -> Feature:
        """Returns vehicle as feature."""

        return Feature(
            id=self.vehicle_id,
            geometry=self.as_point(),
            properties={
                "popupContent": self.as_html_popup(),
                "icon": self.as_html_icon(),
            },
        )

    def as_html_popup(self) -> str:
        """Returns vehicle as html for a popup."""

        bikes = (
            """<img src ="static/bike.png" alt="bikes allowed" title="Bicycles Allowed" width=25 height=25 style="margin:2px;">"""
            if self.trip.bikes_allowed == 1
            else ""
        )
        alert = (
            """<img src ="static/alert.png" alt="alert" width=25 height=25 style="margin:2px;">"""
            if self.trip.alerts
            else ""
        )
        prediction = (
            """<img src="static/train_icon.png" alt="prediction" width=25 height=25 style="margin:2px;">"""
            if self.trip.predictions
            else ""
        )

        html = (
            f"""<a href = {self.trip.route.route_url} style="color:#{self.trip.route.route_color};font-size:28pt;text-decoration: none;text-align: left">"""
            f"""{self.route.route_desc} {self.trip.trip_short_name or self.trip_id}</a></br>"""
            """<body style="color:#ffffff;text-align: left;">"""
            f"""{self.DIRECTION_MAPPER.get(self.direction_id, "Unknown")} to {self.trip.trip_headsign}</body></br>"""
            """—————————————————————————————————</br>"""
            f"""{alert} {prediction} {bikes}</br>"""
            f"""{self.return_current_status()}</br>"""
            f"""Speed: {int(self.speed * 2.23694) if self.speed else "Unknown"} mph</br>"""
            f"""Bearing: {self.bearing}°</br>"""
            f"""<a style="color:grey;font-size:9pt">"""
            f"""Timestamp: {self.updated_at_datetime.strftime("%m/%d/%Y %I:%M%p")}</br>"""
            f"""Route: {self.route.route_short_name or self.route_id}: {self.route_id}</br>"""
            f"""Trip: {self.trip_id}</a>"""
        )
        return html

    def as_html_icon(self) -> str:
        """Returns vehicle as html for an icon."""
        """<img src ="static/bike.png" alt="bikes allowed" title="Bicycles Allowed" width=25 height=25 style="margin:2px;">"""
        html = (
            """<a style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:white;font-family:montserrat,Helvetica,sans-serif">"""
            f"""<img src ="static/icon.png" alt="vehicle" width=50 height=50 style="transform:rotate({self.bearing}deg);">"""
            f"""{self.trip.trip_short_name if self.route.route_type == 2 else ""}</a>"""
        )

        return html
