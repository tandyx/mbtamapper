"""File to hold the CalendarDate class and its associated methods."""

from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, String
from ..base import GTFSBase


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

    def __repr__(self) -> str:
        return f"<CalendarDate(service_id={self.service_id})>"
