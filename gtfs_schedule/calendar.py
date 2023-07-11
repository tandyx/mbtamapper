"""File to hold the Calendar class and its associated methods."""
from datetime import datetime

from sqlalchemy import Integer, Column, String
from sqlalchemy.orm import relationship, reconstructor

from gtfs_loader.gtfs_base import GTFSBase


class Calendar(GTFSBase):
    """Calendar"""

    __tablename__ = "calendars"

    service_id = Column(String, primary_key=True)
    monday = Column(Integer)
    tuesday = Column(Integer)
    wednesday = Column(Integer)
    thursday = Column(Integer)
    friday = Column(Integer)
    saturday = Column(Integer)
    sunday = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)

    calendar_dates = relationship(
        "CalendarDate", back_populates="calendar", passive_deletes=True
    )
    calendar_attributes = relationship(
        "CalendarAttribute", back_populates="calendar", passive_deletes=True
    )
    trips = relationship("Trip", back_populates="calendar", passive_deletes=True)

    @reconstructor
    def init_on_load(self) -> None:
        """Initialize the calendar object on load"""
        # pylint: disable=attribute-defined-outside-init
        self.start_datetime = datetime.strptime(self.start_date, "%Y%m%d")
        self.end_datetime = datetime.strptime(self.end_date, "%Y%m%d")

    def __repr__(self) -> str:
        return f"<Calendar(service_id={self.service_id})>"

    def __str__(self) -> str:
        return f"{self.service_id} - {self.start_date} - {self.end_date}"

    def contains_trips_of_type(self, route_type: str) -> bool:
        """Returns bool of whether service contains trips of a certain route type

        Args:
            route_type (str): The route type to check for
        Returns:
            bool: Whether the service contains trips of the provided route type"""

        return route_type in [trip.route.route_type for trip in self.trips]
