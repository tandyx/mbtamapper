"""File to hold the Calendar class and its associated methods."""
# pylint: disable=line-too-long
from datetime import datetime
from shapely.geometry import Point
from geojson import Feature

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Float, ForeignKey
from gtfs_loader.gtfs_base import GTFSBase

from helper_functions import list_unpack, get_date, get_current_time


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
    facilities = relationship("Facility", back_populates="stop", passive_deletes=True)
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

    def __repr__(self):
        return f"<Stop(stop_id={self.stop_id})>"

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

    def as_feature(self, date: datetime) -> Feature:
        """Returns stop object as a feature.

        Args:
            date: The date to return the feature for.
        Returns:
            A geojson feature.
        """

        return Feature(
            id=self.stop_id,
            geometry=self.as_point(),
            properties={
                "popupContent": self.as_html_popup(date),
                "name": self.stop_name,
            },
        )

    def return_route_color(self, routes: list = None) -> str:
        """Returns the route color for the stop.

        Args:
            routes: A list of routes to return the color for. If None, the stop's routes will be used.
        """
        return next((r.route_color for r in routes or self.routes), "008EAA")

    def as_html_popup(self, date: datetime) -> str:
        """Returns stop object as an html popup.
        Args:
            date: The date to return the popup for."""
        routes = self.routes or self.return_routes()
        stop_color = self.return_route_color(routes)
        alerts = self.alerts or list_unpack(
            ((a for a in s.alerts if not a.trip) for s in self.child_stops), "list"
        )
        stop_time_html = "".join(
            (
                st.as_html()
                for st in sorted(
                    self.stop_times
                    or list_unpack(s.stop_times for s in self.child_stops),
                    key=lambda x: x.departure_seconds,
                )
                if st.trip.calendar.operates_on_date(date)
                and st.departure_seconds
                > (get_current_time().timestamp() - get_date().timestamp())
                and not st.is_destination()
            )
        )

        alert = (
            """<div class = "popup" onclick="showAlertPopup()" >"""
            """<img src ="static/alert.png" alt="alert" width=25 height=25 title = "Show Alerts" style="margin:2px;">"""
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Updated</td></tr>"""
            f"""{"".join({a.as_html() for a in alerts})}</table>"""
            """</span></div>"""
            if alerts
            else ""
        )

        wheelchair = (
            """<div class = "tooltip">"""
            """<img src="static/wheelchair.png" alt="accessible" width=25 height=25 style="margin:2px;">"""
            """<span class="tooltiptext">Wheelchair Accessible.</span></div>"""
            if self.wheelchair_boarding == "1"
            or "1" in [s.wheelchair_boarding for s in self.child_stops]
            else ""
        )

        schedule = (
            """<div class = "popup" onclick="showPredictionPopup()">"""
            """<img src ="static/train_icon.png" alt="schedule" width=25 height=25 title = "Show Departures" style="margin:2px;">"""
            """<span class="popuptext" id="predictionPopup" style="z-index=-1;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Route</td><td>Trip</td><td>Headsign</td><td>Scheduled</td><td>Platform</td></tr>"""
            f"""{stop_time_html}</tr></table>"""
            """</span></div>"""
            if stop_time_html
            else ""
        )

        parking = (
            """<div class = "popup" onclick="showParkingPopup()">"""
            """<img src ="static/parking.png" alt="parking" width=25 height=25 title = "Show Parking" style="margin:2px;">"""
            """<span class="popuptext" id="parkingPopup" style="z-index=-1;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Parking Lot</td><td>Spaces</td><td>Daily Cost</td><td>Payment App</td></tr>"""
            f"""{"".join({p.as_html_row() for p in self.facilities if p.facility_type == "parking-area"})}</tr></table>"""
            """</span></div>"""
            if [p for p in self.facilities if p.facility_type == "parking-area"]
            else ""
        )

        bikes = (
            """<div class = "popup" onclick="showBikePopup()">"""
            """<img src ="static/bike.png" alt="bike" width=25 height=25 title = "Show Bike Parking" style="margin:2px;">"""
            """<span class="popuptext" id="bikePopup" style="z-index=-1;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Bike Parking</td><td>Spaces</td></tr>"""
            f"""{"".join({p.as_html_row(False) for p in self.facilities if p.facility_type == "bike-storage"})}</tr></table>"""
            """</span></div>"""
            if [p for p in self.facilities if p.facility_type == "bike-storage"]
            else ""
        )

        route_colors = ", </a>".join(
            f"<a href = '{r.route_url}' target='_blank' style='color:#{r.route_color or 'ffffff'};text-decoration: none;'>{r.route_short_name or r.route_long_name}"
            for r in routes
        )

        return (
            f"<a href = '{self.stop_url}' target='_blank' style='color:#{stop_color};font-size:28pt;text-decoration: none;text-align: left'>{self.stop_name}</a></br>"
            f"<body style='color:#ffffff;text-align: left;'>"
            f"{self.stop_desc or next((s.stop_desc for s in self.child_stops), self.stop_desc)}</br>"
            f"—————————————————————————————————</br>"
            f"{alert} {schedule} {bikes} {parking} {wheelchair} {'</br>' if any([alert, schedule, wheelchair, bikes, parking]) else ''}"
            f"Routes: {route_colors}</a></br>"
            f"Zones: {', '.join(set(c.zone_id for c in self.child_stops if c.zone_id))}</br>"
            f"<a style='color:grey;font-size:9pt'>"
            f"Address: {self.stop_address}</br>"
            f"Platforms: {', '.join(s.platform_name.strip('Commuter Rail - ') for s in self.child_stops if s.platform_code)}</br>"
            "</a></body>"
        )
