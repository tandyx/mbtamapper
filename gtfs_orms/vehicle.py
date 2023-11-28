"""File to hold the Vehicle class and its associated methods."""
# pylint: disable=line-too-long

from dateutil.parser import isoparse
from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import reconstructor, relationship
from helper_functions import shorten

from .gtfs_base import GTFSBase


class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"

    vehicle_id = Column(String)
    trip_id = Column(String)
    route_id = Column(String)
    direction_id = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    bearing = Column(Float)
    current_stop_sequence = Column(Integer)
    current_status = Column(String)
    timestamp = Column(String)
    stop_id = Column(String)
    label = Column(String)
    occupancy_status = Column(String)
    occupancy_percentage = Column(Integer)
    speed = Column(Float)
    index = Column(Integer, primary_key=True)

    predictions = relationship(
        "Prediction",
        back_populates="vehicle",
        primaryjoin="Vehicle.trip_id==foreign(Prediction.trip_id)",
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

    DIRECTION_MAPPER = {
        "0": "Outbound",
        "1": "Inbound",
        "1.0": "Inbound",
        "0.0": "Outbound",
    }

    STATUS_MAPPER = {
        "0": "Incoming at ",
        "1": "Stopped at ",
        "2": "In transit to ",
    }

    REALTIME_NAME = "vehicle_positions"

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.updated_at_datetime = isoparse(self.timestamp)
        self.bearing = self.bearing or 0
        self.current_stop_sequence = self.current_stop_sequence or 0

    def return_current_status(self) -> str:
        """Returns current status of vehicle."""

        if self.stop:
            current_status = (
                f"""<span>{Vehicle.STATUS_MAPPER.get(self.current_status, "In transit to ")} </span>"""
                f"""<a href={self.stop.stop_url} target="_blank">{self.stop.stop_name}{(' - ' + self.stop.platform_name) if self.stop.platform_code else ''}</a>  """
                f"""{("— " + self.next_stop_prediction.predicted.strftime("%I:%M %p")) if self.next_stop_prediction and self.next_stop_prediction.predicted and self.current_status != "1" else ""}"""
            )
        else:
            current_status = ""

        return f"<span>{current_status}</span>" + ("</br>" if current_status else "")

    def as_point(self) -> Point:
        """Returns vehicle as point."""
        return Point(self.longitude, self.latitude)

    def as_feature(self) -> Feature:
        """Returns vehicle as feature."""

        return Feature(
            id=self.vehicle_id,
            geometry=self.as_point(),
            properties={
                "popupContent": self.as_html_popup(),
                "icon": self.as_html_icon(),
                "name": shorten(
                    self.trip.trip_short_name or self.trip_id
                    if self.trip
                    else self.trip_id
                ),
            },
        )

    def __get_occupancy_color(self) -> str:
        """Returns a color based on the occupancy.

        Args:
            occupancy (int): occupancy percentage"""

        occupancy_dict = {
            "#ffffff": self.occupancy_percentage < 40,  # white
            "#ffff00": 40 <= self.occupancy_percentage < 60,
            "#ff8000": 60 <= self.occupancy_percentage < 80,
            "#ff0000": self.occupancy_percentage >= 80,
        }

        for color, condition in occupancy_dict.items():
            if condition:
                return color

    def as_html_popup(self) -> str:
        """Returns vehicle as html for a popup."""

        predicted_html = "".join(p.as_html() for p in self.predictions if p.predicted)

        occupancy = (
            f"""Occupancy: <span style="color:{self.__get_occupancy_color()}">{int(self.occupancy_percentage)}%</span></br>"""
            if self.occupancy_status
            else ""
        )

        bikes = (
            """<div class = "tooltip-mini_image" onmouseover="hoverImage('bikeImg')" onmouseleave="unhoverImage('bikeImg')">"""
            """<img src ="static/img/bike.png" alt="bike" class="mini_image" id="bikeImg" >"""
            """<span class="tooltiptext-mini_image" >Bikes allowed.</span></div>"""
            if self.trip and self.trip.bikes_allowed == 1
            else ""
        )
        alert = (
            """<div class = "popup" onclick="openMiniPopup('alertPopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('alertImg')" onmouseleave="unhoverImage('alertImg')">"""
            """<span class = 'tooltiptext-mini_image' >Show Alerts</span>"""
            """<img src ="static/img/alert.png" alt="alert" class="mini_image" id="alertImg" >"""
            "</span>"
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Updated</td></tr>"""
            f"""{"".join(set(a.as_html() for a in self.trip.alerts)) if self.trip else ""}</table>"""
            """</span></div>"""
            if self.trip and self.trip.alerts
            else ""
        )

        prediction = (
            """<div class = "popup" onclick="openMiniPopup('predictionPopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('predictionImg')" onmouseleave="unhoverImage('predictionImg')">"""
            """<span class = 'tooltiptext-mini_image' >Show Predictions</span>"""
            """<img src ="static/img/train_icon.png" alt="prediction" class="mini_image" id="predictionImg">"""
            "</span>"
            """<span class="popuptext" id="predictionPopup" style="width:1850%;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{self.route.route_color if self.route else "000000"};font-weight:bold;">"""
            """<td>Stop</td><td>Platform</td><td>Predicted</td></tr>"""
            f"""{predicted_html}</table>"""
            """</span></div>"""
            if predicted_html
            else ""
        )

        prd_status = (
            self.next_stop_prediction.status_as_html()
            if self.next_stop_prediction
            else ""
        )

        return (
            f"""<a href = {self.route.route_url if self.route else ""} target="_blank"  class = 'popup_header' style="color:#{self.route.route_color if self.route else ""};">"""
            f"""{(self.trip.trip_short_name if self.trip else None) or shorten(self.trip_id)}</a></br>"""
            """<body style="color:#ffffff;text-align: left;">"""
            f"""{Vehicle.DIRECTION_MAPPER.get(self.direction_id, "Unknown")} to {self.trip.trip_headsign if self.trip else max(self.predictions, key=lambda x: x.stop_sequence).stop.stop_name if self.predictions else "Unknown"}</body></br>"""
            # """<hr/>"""
            """—————————————————————————————————</br>"""
            f"""{alert} {prediction} {bikes} {"</br>" if any([alert, prediction, bikes]) else ""}"""
            f"{self.return_current_status()}"
            f"""{("Delay: " if prd_status else "") + prd_status}{"</br>" if prd_status else ""}"""
            f"""{occupancy}"""
            f"""Speed: {int(self.speed or 0) if self.speed is not None or self.current_status == "1" or self.route.route_type in ["0", "2"] else "Unknown"} mph</br>"""
            # f"""Bearing: {self.bearing}°</br>"""
            f"""<span class = "popup_footer">"""
            f"""Vehicle: {self.vehicle_id}</br>"""
            f"""Route: {f'({self.route.route_short_name}) ' if self.route and self.route.route_type == "3" else ""}{self.route.route_long_name if self.route else self.route_id}</br>"""
            f"""Timestamp: {self.updated_at_datetime.strftime("%m/%d/%Y %I:%M %p")}</br></span>"""
        )

    def as_html_icon(self) -> str:
        """Returns vehicle as html for an icon."""
        return (
            """<span class="vehicle_wrapper">"""
            f"""<img src ="static/img/icon.png" alt="vehicle" width=65 height=65 style="transform:rotate({self.bearing}deg);{self.route.filter}">"""
            """<span class="vehicle_text">"""
            f"""{self.trip.trip_short_name if self.trip and self.trip.trip_short_name else self.route.route_short_name if self.route and (self.route.route_type == "3" or self.route_id.startswith("Green")) and self.route.route_short_name else ""}</span></span>"""
        )
