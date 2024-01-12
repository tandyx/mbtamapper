"""File to hold the CalendarDate class and its associated methods."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase


class CalendarDate(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Dates"""

    __tablename__ = "calendar_dates"
    __filename__ = "calendar_dates.txt"

    service_id = mapped_column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    date = mapped_column(String, primary_key=True)
    exception_type = mapped_column(String)
    holiday_name = mapped_column(String)

    calendar = relationship("Calendar", back_populates="calendar_dates")
