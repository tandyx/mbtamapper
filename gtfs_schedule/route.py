"""File to hold the Calendar class and its associated methods."""
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, Column, String
from gtfs_loader.gtfs_base import GTFSBase


class Route(GTFSBase):
    """Route"""

    __tablename__ = "routes"

    route_id = Column(String, primary_key=True)
    agency_id = Column(String)
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
        exclude = ["_sa_instance_state", "trips", "all_trips", "multi_route_trips"]
        return {k: v for k, v in self.__dict__.items() if v and k not in exclude}
