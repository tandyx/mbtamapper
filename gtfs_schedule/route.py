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
