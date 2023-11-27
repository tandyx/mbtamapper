"""File to hold the Route class and its associated methods."""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import reconstructor, relationship

from helper_functions import get_current_time

from ..base import GTFSBase

# pylint: disable=line-too-long


class Route(GTFSBase):
    """Route"""

    __tablename__ = "routes"
    __filename__ = "routes.txt"

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

    HEX_TO_CSS = {
        "FFC72C": "filter: invert(66%) sepia(78%) saturate(450%) hue-rotate(351deg) brightness(108%) contrast(105%);",
        "7C878E": "filter: invert(57%) sepia(2%) saturate(1547%) hue-rotate(160deg) brightness(91%) contrast(103%);",
        "003DA5": "filter: invert(13%) sepia(61%) saturate(5083%) hue-rotate(215deg) brightness(96%) contrast(101%);",
        "008EAA": "filter: invert(40%) sepia(82%) saturate(2802%) hue-rotate(163deg) brightness(88%) contrast(101%);",
        "80276C": "filter: invert(20%) sepia(29%) saturate(3661%) hue-rotate(283deg) brightness(92%) contrast(93%);",
        "006595": "filter: invert(21%) sepia(75%) saturate(2498%) hue-rotate(180deg) brightness(96%) contrast(101%);",
        "00843D": "filter: invert(31%) sepia(99%) saturate(684%) hue-rotate(108deg) brightness(96%) contrast(101%);",
        "DA291C": "filter: invert(23%) sepia(54%) saturate(7251%) hue-rotate(355deg) brightness(90%) contrast(88%);",
        "ED8B00": "filter: invert(46%) sepia(89%) saturate(615%) hue-rotate(1deg) brightness(103%) contrast(104%);",
        "ffffff": "filter: invert(100%) sepia(93%) saturate(19%) hue-rotate(314deg) brightness(105%) contrast(104%);",
    }

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database."""
        # pylint: disable=attribute-defined-outside-init
        self.route_url = (
            self.route_url or f"https://www.mbta.com/schedules/{self.route_id}"
        )
        self.route_name = self.route_short_name or self.route_long_name
        self.filter = Route.HEX_TO_CSS.get(self.route_color, Route.HEX_TO_CSS["ffffff"])
        self.opacity_dict = {
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

    def __repr__(self) -> str:
        return f"<Route(route_id={self.route_id})>"

    def as_html_popup(self) -> str:
        """Return a proper HTML popup representation of the route object"""
        alert_row = "".join(
            set(a.as_html() for a in self.alerts if not a.stop and not a.trip)
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
            f"""{alert_row}</table>"""
            """</span></div>"""
            if alert_row
            else ""
        )

        return (
            f"""<a href = {self.route_url} target="_blank"  style="color:#{self.route_color};font-size:28pt;"> {self.route_name} </a></br>"""
            f"""<body style="color:#ffffff;text-align: left;"> {self.route_desc} - {self.route_long_name} </br>"""
            "—————————————————————————————————</br>"
            f"{alert} {'</br>' if alert else ''}"
            f"Agency: {self.agency.as_html()} </br>"
            f"Fare Class: {self.route_fare_class} </br>"
            """<span class="popup_footer">"""
            f"Route ID: {self.route_id} </br>"
            f"Timestamp: {get_current_time().strftime('%m/%d/%Y %I:%M %p')} </br>"
            "</span></body>"
        )

    def as_html_dict(self) -> dict[str]:
        """Return HTML + other data in a dictionary"""

        return {
            "name": self.route_short_name or self.route_long_name,
            "color": "#" + self.route_color,
            "opacity": self.opacity_dict.get(self.route_desc, 0.5),
            "weight": Route.WEIGHT,
            "popupContent": self.as_html_popup(),
            "is_added": self.network_id == "rail_replacement_bus",
        }
