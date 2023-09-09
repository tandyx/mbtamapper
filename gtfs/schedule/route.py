"""File to hold the Route class and its associated methods."""
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy import Column, String, ForeignKey, Integer
from ..gtfs_base import GTFSBase

from helper_functions import get_current_time

# pylint: disable=line-too-long


class Route(GTFSBase):
    """Route"""

    __tablename__ = "routes"

    route_id = Column(String, primary_key=True)
    agency_id = Column(
        String, ForeignKey("agencies.agency_id", ondelete="CASCADE", onupdate="CASCADE")
    )
    route_short_name = Column(String)
    route_long_name = Column(String)
    route_desc = Column(String)
    route_type = Column(String)
    route_url = Column(String)
    route_color = Column(String)
    route_text_color = Column(String)
    route_sort_order = Column(Integer)
    route_fare_class = Column(String)
    line_id = Column(String)
    listed_route = Column(String)
    network_id = Column(String)

    agency = relationship("Agency", back_populates="routes")
    multi_route_trips = relationship(
        "MultiRouteTrip", back_populates="route", passive_deletes=True
    )
    trips = relationship("Trip", back_populates="route", passive_deletes=True)
    all_trips = relationship(
        "Trip",
        primaryjoin="""or_(
            foreign(Trip.route_id)==Route.route_id, 
            and_(Trip.trip_id==remote(MultiRouteTrip.trip_id), 
            Route.route_id==foreign(MultiRouteTrip.added_route_id))
            )""",
        viewonly=True,
    )
    predictions = relationship(
        "Prediction",
        back_populates="route",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    vehicles = relationship(
        "Vehicle",
        back_populates="route",
        primaryjoin="foreign(Vehicle.route_id)==Route.route_id",
        viewonly=True,
    )
    alerts = relationship(
        "Alert",
        back_populates="route",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )

    WEIGHT = 0.8

    @reconstructor
    def init_on_load(self):
        self.route_url = (
            self.route_url or f"https://www.mbta.com/schedules/{self.route_id}"
        )

    def __repr__(self) -> str:
        return f"<Route(route_id={self.route_id})>"

    def as_html_popup(self) -> str:
        """Return a proper HTML popup representation of the route object"""
        alert_row = "".join(
            set(a.as_html() for a in self.alerts if not a.stop and not a.trip)
        )
        alert = (
            """<span class = 'tooltip'>"""
            """<span class = 'tooltiptext-mini_image'>Show Alerts</span>"""
            """<div class = "popup" onclick="openMiniPopup('alertPopup')" >"""
            """<img src ="static/img/alert.png" alt="alert" class="mini_image">"""
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Updated</td></tr>"""
            f"""{alert_row}</table>"""
            """</span></div></span>"""
            if alert_row
            else ""
        )

        return (
            f"""<a href = {self.route_url} target="_blank"  style="color:#{self.route_color};font-size:28pt;"> {self.route_short_name or self.route_long_name} </a></br>"""
            f"""<body style="color:#ffffff;text-align: left;"> {self.route_desc} - {self.route_long_name} </br>"""
            "—————————————————————————————————</br>"
            f"{alert} {'</br>' if alert else ''}"
            f"Agency: {self.agency.as_html()} </br>"
            f"Fare Class: {self.route_fare_class} </br>"
            """<a style="color:grey;font-size:9pt">"""
            f"Route ID: {self.route_id} </br>"
            f"Timestamp: {get_current_time().strftime('%m/%d/%Y %I:%M %p')} </br>"
            "</a></body>"
        )

    def as_html_dict(self) -> dict[str]:
        """Return HTML + other data in a dictionary"""

        opacity_dict = {
            "Community Bus": 0.35,
            "Local Bus": 0.5,
            "Express Bus": 0.75,
            "Commuter Bus": 0.75,
            "Rail Replacement Bus": 0.75,
            "Key Bus": 0.9 if self.line_id == "sl_rapid_transit" else 0.75,
            "Rapid Transit": 0.9,
            "Commuter Rail": 0.9,
            "Ferry": 0.9,
        }

        return {
            "name": self.route_short_name or self.route_long_name,
            "color": "#" + self.route_color,
            "opacity": opacity_dict.get(self.route_desc, 0.5),
            "weight": Route.WEIGHT,
            "popupContent": self.as_html_popup(),
            "is_added": self.network_id == "rail_replacement_bus",
        }
