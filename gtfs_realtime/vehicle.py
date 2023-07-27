"""Vehicle"""
# pylint: disable=line-too-long

from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor


from shapely.geometry import Point
from geojson import Feature

from gtfs_loader.gtfs_base import GTFSBase
from helper_functions import hex_to_css


# filter: invert(23%) sepia(76%) saturate(4509%) hue-rotate(353deg) brightness(88%) contrast(92%);
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

    DIRECTION_MAPPER = {"0": "Outbound", "1": "Inbound"}
    CURRENT_STATUS_MAPPER = {
        "0": "Incoming at ",
        "1": "Stopped at ",
        "2": "In transit to ",
    }

    @reconstructor
    def init_on_load(self):
        """Converts updated_at to datetime object."""
        # pylint: disable=attribute-defined-outside-init
        self.updated_at_datetime = isoparse(self.timestamp)
        self.current_stop_sequence = self.current_stop_sequence or 0

    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id})>"

    def return_current_status(self) -> str:
        """Returns current status of vehicle."""
        prd_status = (
            self.next_stop_prediction.status_as_html()
            if self.next_stop_prediction
            else ""
        )

        if self.stop:
            current_status = (
                f"""<a style="color:#ffffff">{self.CURRENT_STATUS_MAPPER.get(self.current_status, "In transit to ")} </a>"""
                f"""<a href={self.stop.stop_url} target="_blank" style='text-decoration:none;color:#{self.route.route_color};'>{self.stop.stop_name}{(' - ' + self.stop.platform_name) if self.stop.platform_code else ''}</a>  """
                f"""{("— " + self.next_stop_prediction.predicted.strftime("%I:%M %p")) if self.next_stop_prediction and self.next_stop_prediction.predicted and self.current_status != "1" else ""} {prd_status}"""
            )
        else:
            current_status = prd_status

        return f"<a>{current_status}</a>" + ("</br>" if current_status else "")

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
            },
        )

    def as_html_popup(self) -> str:
        """Returns vehicle as html for a popup."""

        predicted_html = "".join(p.as_html() for p in self.predictions if p.predicted)

        bikes = (
            """<div class = "tooltip">"""
            """<img src ="static/bike.png" alt="bike" width=25 height=25 style="margin:2px;">"""
            """<span class="tooltiptext">Bikes allowed.</span></div>"""
            if self.trip and self.trip.bikes_allowed == 1
            else ""
        )
        alert = (
            """<div class = "popup" onclick="showAlertPopup()" >"""
            """<img src ="static/alert.png" title="Show Alerts" alt="alert" width=25 height=25 style="margin:2px;">"""
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Updated</td></tr>"""
            f"""{"".join(set(a.as_html() for a in self.trip.alerts if not a.stop)) if self.trip else ""}</table>"""
            """</span></div>"""
            if self.trip and self.trip.alerts
            else ""
        )

        prediction = (
            """<div class = "popup" onclick="showPredictionPopup()">"""
            """<img src ="static/train_icon.png" alt="prediction" width=25 height=25 title = "Show Predictions" style="margin:2px;">"""
            """<span class="popuptext" id="predictionPopup" style="z-index=-1;width:1850%;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{self.route.route_color if self.route else "000000"};font-weight:bold;">"""
            """<td>Stop</td><td>Platform</td><td>Predicted</td></tr>"""
            f"""{predicted_html}</table>"""
            """</span></div>"""
            if predicted_html
            else ""
        )

        return (
            f"""<a href = {self.route.route_url if self.route else ""} target="_blank"  style="color:#{self.route.route_color if self.route else ""};font-size:28pt;text-decoration: none;text-align: left">"""
            f"""{(self.trip.trip_short_name if self.trip else None) or self.trip_id}</a></br>"""
            """<body style="color:#ffffff;text-align: left;">"""
            f"""{self.DIRECTION_MAPPER.get(self.direction_id, "Unknown")} to {self.trip.trip_headsign if self.trip else max(self.predictions, key=lambda x: x.stop_sequence).stop.stop_name if self.predictions and max(self.predictions, key=lambda x: x.stop_sequence).stop else "Unknown"}</body></br>"""
            """—————————————————————————————————</br>"""
            f"""{alert} {prediction} {bikes} {"</br>" if any([alert, prediction, bikes]) else ""}"""
            f"{self.return_current_status()}"
            f"""Speed: {int(self.speed or 0) if self.speed is not None or self.current_status == "1" else "Unknown"} mph</br>"""
            f"""Bearing: {self.bearing}°</br>"""
            f"""<a style="color:grey;font-size:9pt">"""
            f"""Vehicle: {self.vehicle_id}</br>"""
            f"""Route: {f'({self.route.route_short_name}) ' if self.route and self.route.route_type == "3" else ""}{self.route.route_long_name if self.route else self.route_id}</br>"""
            f"""Timestamp: {self.updated_at_datetime.strftime("%m/%d/%Y %I:%M %p")}</br>"""
        )

    def as_html_icon(self) -> str:
        """Returns vehicle as html for an icon."""
        return (
            """<a style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);">"""
            f"""<img src ="static/icon.png" alt="vehicle" width=65 height=65 style="transform:rotate({self.bearing}deg);{hex_to_css(self.route.route_color if self.route else "ffffff")}">"""
            """<a style="position:absolute;top:35%;left:45%;transform:translate(-50%,-50%);color:white;font-family:'montserrat','Helvetica',sans-serif;">"""
            f"""{self.trip.trip_short_name if self.route and self.route.route_type == "2" else ""}</a></a>"""
        )
