"""File to hold the CalendarDate class and its associated methods."""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .gtfs_base import GTFSBase


class CalendarDate(GTFSBase):
    """Calendar Dates"""

    __tablename__ = "calendar_dates"
    __filename__ = "calendar_dates.txt"

    service_id = Column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    date = Column(String, primary_key=True)
    exception_type = Column(String)
    holiday_name = Column(String)

    calendar = relationship("Calendar", back_populates="calendar_dates")
