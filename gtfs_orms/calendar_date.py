"""File to hold the CalendarDate class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .calendar import Calendar


class CalendarDate(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Dates"""

    __tablename__ = "calendar_dates"
    __filename__ = "calendar_dates.txt"

    service_id: str = mapped_column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    date: str = mapped_column(String, primary_key=True)
    exception_type: Optional[str] = mapped_column(String)
    holiday_name: Optional[str] = mapped_column(String)

    calendar: "Calendar" = relationship("Calendar", back_populates="calendar_dates")
