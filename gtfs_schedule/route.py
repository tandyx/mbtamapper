"""File to hold the Calendar class and its associated methods."""
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Integer
from gtfs_loader.gtfs_base import GTFSBase


class Route(GTFSBase):
    """Route"""

    __tablename__ = "routes"

    route_id = Column(String, primary_key=True)
    agency_id = Column(String, ForeignKey("agencies.agency_id"))
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

    def __repr__(self) -> str:
        return f"<Route(route_id={self.route_id})>"

    def as_dict(self) -> dict[str]:
        """Return a proper dictionary representation of the route object"""

        dictionary = {
            "route_id": self.route_id,
            "agency_id": self.agency_id,
            "route_short_name": self.route_short_name,
            "route_long_name": self.route_long_name,
            "route_desc": self.route_desc,
            "route_type": self.route_type,
            "route_url": self.route_url,
            "route_color": "#" + self.route_color,
            "route_text_color": "#" + self.route_text_color,
            "route_sort_order": self.route_sort_order,
            "route_fare_class": self.route_fare_class,
            "line_id": self.line_id,
            "listed_route": self.listed_route,
            "network_id": self.network_id,
            "agency_name": self.agency.agency_name,
            "agency_url": self.agency.agency_url,
            "agency_phone": self.agency.agency_phone,
            "alerts": [a.as_dict() for a in self.alerts if not a.trip_id],
            "active_trips": [t.as_label() for t in self.trips if t.active],
        }

        return dictionary

    def as_html_popup(self) -> str:
        """Return a proper HTML popup representation of the route object"""
        alert_row = "".join(
            set(a.as_html() for a in self.alerts if not a.stop and not a.trip)
        )
        alert = (
            """<div class = "popup" onclick="showAlertPopup()" >"""
            """<img src ="static/alert.png" alt="alert" width=25 height=25 style="margin:2px;">"""
            """<span class="popuptext" id="alertPopup">"""
            """<table class = "table">"""
            f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
            """<td>Alert</td><td>Updated</td></tr>"""
            f"""{alert_row}</table>"""
            """</span></div>"""
            if alert_row
            else ""
        )

        html = (
            f"""<a href = {self.route_url} target="_blank"  style="color:#{self.route_color};font-size:28pt;text-decoration: none;text-align: left"> {self.route_short_name or self.route_long_name} </a></br>"""
            f"""<body style="color:#ffffff;text-align: left;"> {self.route_desc} - {self.route_long_name} </br>"""
            "—————————————————————————————————</br>"
            f"{alert} {'</br>' if alert else ''}"
            f"Agency: {self.agency.as_html()} </br>"
            f"Fare Class: {self.route_fare_class} </br>"
            """<a style="color:grey;font-size:9pt">"""
            f"Route ID: {self.route_id} </br>"
            f"Route Type: {self.route_type} </br>"
            f""
            "</a></body>"
        )

        return html

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

        dictionary = {
            "name": self.route_short_name or self.route_long_name,
            "color": "#" + self.route_color,
            "opacity": opacity_dict.get(self.route_desc, 0.5),
            "weight": Route.WEIGHT,
            "popupContent": self.as_html_popup(),
            "is_added": self.network_id == "rail_replacement_bus",
        }

        return dictionary
