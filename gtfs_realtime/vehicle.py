"""Vehicle"""

import os
import logging
import pandas as pd
import requests as rq

from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, reconstructor, Session


from shapely.geometry import Point
from geojson import Feature

from gtfs_loader.gtfs_base import GTFSBase
from shared_code.to_sql import to_sql
from shared_code.color_mapping import return_delay_colors, hex_to_css


RENAME_DICT = {
    "id": "vehicle_id",
    "type": "vehicle_type",
    "attributes_bearing": "bearing",
    "attributes_current_status": "current_status",
    "attributes_current_stop_sequence": "current_stop_sequence",
    "attributes_direction_id": "direction_id",
    "attributes_label": "label",
    "attributes_latitude": "latitude",
    "attributes_longitude": "longitude",
    "attributes_occupancy_status": "occupancy_status",
    "attributes_speed": "speed",
    "attributes_updated_at": "updated_at",
    "links_self": "links_self",
    "relationships_route_data_id": "route_id",
    "relationships_stop_data_id": "stop_id",
    "relationships_trip_data_id": "trip_id",
}


# filter: invert(23%) sepia(76%) saturate(4509%) hue-rotate(353deg) brightness(88%) contrast(92%);
class Vehicle(GTFSBase):
    """Vehicle"""

    __tablename__ = "vehicles"

    vehicle_id = Column(String)
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
    index = Column(Integer, primary_key=True)

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
        prd_status = (
            self.next_stop_prediction.status_as_html()
            if self.next_stop_prediction
            else "<a style ='color:#ffffff;'> (Delay Unknown)</a>"
        )

        if self.stop:
            current_status = (
                f"""<a style="color:#ffffff;">Vehicle {self.label or self.vehicle_id} </a>"""
                f"""{self.current_status.lower().replace("_", " ")} """
                f"""<a href={self.stop.stop_url} style='text-decoration:none;color:#{self.route.route_color};'>{self.stop.stop_name}{(' - ' + self.stop.platform_name) if self.stop.platform_code else ''}</a>  """
                f"""{prd_status}"""
            )
        else:
            current_status = (
                f"""<a style="color:#ffffff;">Vehicle {self.label or self.vehicle_id} on </a>"""
                f"""<a href={self.route.route_url if self.route else ""} style='text-decoration:none;color:#{self.route.route_color if self.route else ""};'>{self.route.route_long_name if self.route else self.route_id}</a>"""
                f"""{prd_status}"""
            )
        return current_status

    def as_point(self) -> Point:
        """Returns vehicle as point."""
        return Point(self.latitude, self.longitude)

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
            """<div class = "tooltip">"""
            """<img src ="static/bike.png" alt="bike" width=25 height=25 style="margin:2px;">"""
            """<span class="tooltiptext">Bicycles are allowed on this trip.</span></div>"""
            if self.trip and self.trip.bikes_allowed == 1
            else ""
        )
        alert = (
            """<div class = "popup" onclick="showAlertPopup()" >"""
            """<img src ="static/alert.png" title="Show Alerts" alt="alert" width=25 height=25 style="margin:2px;">"""
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Header</td><td>Created</td><td>Updated</td></tr>"""
            f"""{"".join(set(a.as_html() for a in self.trip.alerts)) if self.trip else ""}</table>"""
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
            f"""{"".join(p.as_html() for p in sorted((p for p in self.predictions if p.predicted), key = lambda x: x.predicted))}</table>"""
            """</span></div>"""
            if self.trip and self.trip.predictions
            else ""
        )

        html = (
            f"""<a href = {self.route.route_url if self.route else ""} style="color:#{self.route.route_color if self.route else ""};font-size:28pt;text-decoration: none;text-align: left">"""
            f"""{(self.trip.trip_short_name if self.trip else None) or self.trip_id}</a></br>"""
            """<body style="color:#ffffff;text-align: left;">"""
            f"""{self.DIRECTION_MAPPER.get(self.direction_id, "Unknown")} to {self.trip.trip_headsign if self.trip else next((p.stop.stop_name for p in self.predictions), "Unknown")}</body></br>"""
            """—————————————————————————————————</br>"""
            f"""{alert} {prediction} {bikes} {"</br>" if any([alert, prediction, bikes]) else ""}"""
            f"""<a >{self.return_current_status()}</a></br>"""
            f"""Speed: {int(self.speed * 2.23694) if self.speed is not None else "Unknown"} mph</br>"""
            f"""Bearing: {self.bearing}°</br>"""
            f"""<a style="color:grey;font-size:9pt">"""
            f"""Timestamp: {self.updated_at_datetime.strftime("%m/%d/%Y %I:%M %p")}</br>"""
            f"""Route: {self.route.route_long_name if self.route else ""} - {self.route_id}</br>"""
            f"""Trip: {self.trip_id}</a>"""
        )
        return html

    def as_html_icon(self) -> str:
        """Returns vehicle as html for an icon."""
        html = (
            """<a style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);">"""
            f"""<img src ="static/icon.png" alt="vehicle" width=65 height=65 style="transform:rotate({self.bearing}deg);{hex_to_css(self.route.route_color if self.route else "ffffff")}">"""
            """<a style="position:absolute;top:35%;left:50%;transform:translate(-50%,-50%);color:white;font-family:montserrat,Helvetica,sans-serif;">"""
            f"""{self.trip.trip_short_name if self.route and self.route.route_type == "2" else ""}</a></a>"""
        )

        return html

    def get_realtime(
        self,
        session: Session,
        route_types: str,
        base_url: str = None,
        api_key: str = None,
    ) -> None:
        """Downloads realtime vehicle data from the mbta api.

        Args:
            engine (Engine): database engine
            route_types (str): comma sep str of route types to query
            base_url (str, optional): base url for api. Defaults to env var.
            api_key (str, optional): api key for api. Defaults to env var."""

        url = (
            (base_url or os.environ.get("MBTA_API_URL"))
            + "/vehicles?filter[route_type]="
            + route_types
            + "&include=trip,stop,route&api_key="
            + (api_key or os.environ.get("MBTA_API_Key"))
        )

        req = rq.get(url, timeout=500)

        if req.ok and req.json().get("data"):
            dataframe = pd.json_normalize(req.json()["data"], sep="_")
        else:
            logging.error("Failed to query vehicles: %s", req.text)
            dataframe = pd.DataFrame()

        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in RENAME_DICT],
            axis=1,
            inplace=True,
        )
        dataframe.rename(columns=RENAME_DICT, inplace=True)
        dataframe.reset_index(inplace=True)
        to_sql(session, dataframe, self.__class__, True)
