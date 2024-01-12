"""File to hold the Stop class and its associated methods."""
# pylint: disable=line-too-long
from datetime import datetime

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from helper_functions import get_current_time, list_unpack

from .gtfs_base import GTFSBase


class Stop(GTFSBase):
    """Stop"""

    __tablename__ = "stops"
    __filename__ = "stops.txt"

    stop_id = mapped_column(String, primary_key=True)
    stop_code = mapped_column(String)
    stop_name = mapped_column(String)
    stop_desc = mapped_column(String)
    platform_code = mapped_column(String)
    platform_name = mapped_column(String)
    stop_lat = mapped_column(Float)
    stop_lon = mapped_column(Float)
    zone_id = mapped_column(String)
    stop_address = mapped_column(String)
    stop_url = mapped_column(String)
    level_id = mapped_column(String)
    location_type = mapped_column(String)
    parent_station = mapped_column(
        String, ForeignKey("stops.stop_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    wheelchair_boarding = mapped_column(String)
    municipality = mapped_column(String)
    on_street = mapped_column(String)
    at_street = mapped_column(String)
    vehicle_type = mapped_column(String)

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
        alerts = self.alerts or list(
            list_unpack(((a for a in s.alerts if not a.trip) for s in self.child_stops))
        )
        stop_time_html = "".join(
            (
                st.as_html()
                for st in sorted(
                    self.stop_times
                    or list_unpack(s.stop_times for s in self.child_stops),
                    key=lambda x: x.departure_seconds,
                )
                if st.is_active(date)
            )
        )

        alert = (
            """<div class = "popup" onclick="openMiniPopup('alertPopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('alertImg')" onmouseleave="unhoverImage('alertImg')">"""
            """<span class = 'tooltiptext-mini_image'>Show Alerts</span>"""
            """<img src ="static/img/alert.png" alt="alert" class="mini_image" id="alertImg">"""
            "</span>"
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
            """<div class = "tooltip-mini_image" onmouseover="hoverImage('whImg')" onmouseleave="unhoverImage('whImg')">"""
            """<img src="static/img/wheelchair.png" alt="accessible" class="mini_image" id="whImg">"""
            """<span class="tooltiptext-mini_image">Wheelchair Accessible.</span></div>"""
            if self.wheelchair_boarding == "1"
            or "1" in [s.wheelchair_boarding for s in self.child_stops]
            else ""
        )

        schedule = (
            """<div class = "popup" onclick="openMiniPopup('predictionPopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('predictionImg')" onmouseleave="unhoverImage('predictionImg')">"""
            """<span class = 'tooltiptext-mini_image'>Show Schedule</span>"""
            """<img src ="static/img/train_icon.png" alt="schedule" class="mini_image" id="predictionImg" >"""
            "</span>"
            """<span class="popuptext" id="predictionPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Route</td><td>Trip</td><td>Headsign</td><td>Scheduled</td><td>Platform</td></tr>"""
            f"""{stop_time_html}</tr></table>"""
            """</span></div>"""
            if stop_time_html
            else ""
        )

        parking = (
            """<div class = "popup" onclick="openMiniPopup('parkingPopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('parkingImg')" onmouseleave="unhoverImage('parkingImg')">"""
            """<span class = 'tooltiptext-mini_image'>Show Parking</span>"""
            """<img src ="static/img/parking.png" alt="parking" class="mini_image" id="parkingImg" >"""
            "</span>"
            """<span class="popuptext" id="parkingPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Parking Lot</td><td>Spaces</td><td>Daily Cost</td><td>Payment App</td></tr>"""
            f"""{"".join({p.as_html_row() for p in self.facilities if p.facility_type == "parking-area"})}</tr></table>"""
            """</span></div>"""
            if any(p for p in self.facilities if p.facility_type == "parking-area")
            else ""
        )

        bikes = (
            """<div class = "popup" onclick="openMiniPopup('bikePopup')">"""
            """<span class = 'tooltip-mini_image' onmouseover="hoverImage('bikeImg')" onmouseleave="unhoverImage('bikeImg')">"""
            """<span class = 'tooltiptext-mini_image'>Show Bike Parking</span>"""
            """<img src ="static/img/bike.png" alt="bike" class="mini_image" id="bikeImg" >"""
            "</span>"
            """<span class="popuptext" id="bikePopup" style="width: 1000%;">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#{stop_color};font-weight:bold;">"""
            """<td>Bike Parking</td><td>Spaces</td></tr>"""
            f"""{"".join({p.as_html_row(False) for p in self.facilities if p.facility_type == "bike-storage"})}</tr></table>"""
            """</span></div>"""
            if [p for p in self.facilities if p.facility_type == "bike-storage"]
            else ""
        )

        route_colors = ", </a>".join(
            f"<a href = '{r.route_url}' target='_blank' style='color:#{r.route_color or 'ffffff'};'>{r.route_short_name or r.route_long_name}"
            for r in routes
        )

        return (
            f"<a href = '{self.stop_url}' target='_blank' class='popup_header' rel='noopener' style='color:#{stop_color}'>{self.stop_name}</a></br>"
            f"<body style='color:#ffffff;text-align: left;'>"
            f"{self.stop_desc or next((s.stop_desc for s in self.child_stops), self.stop_desc)}</br>"
            f"—————————————————————————————————</br>"
            f"{alert} {schedule} {bikes} {parking} {wheelchair} {'</br>' if any([alert, schedule, wheelchair, bikes, parking]) else ''}"
            f"Routes: {route_colors}</a></br>"
            f"Zones: {', '.join(set(c.zone_id for c in self.child_stops if c.zone_id))}</br>"
            f"<span class='popup_footer'>"
            f"Address: {self.stop_address}</br>"
            # f"Platforms: {', '.join(s.platform_name.strip('Commuter Rail - ') for s in self.child_stops if s.platform_code)}</br>"
            f"Timestamp: {get_current_time().strftime('%m/%d/%Y %I:%M %p')}</br>"
            "</span></body>"
        )
