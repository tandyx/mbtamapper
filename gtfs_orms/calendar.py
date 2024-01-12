"""File to hold the Calendar class and its associated methods."""
from datetime import datetime

import pytz
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase


class Calendar(GTFSBase):
    """Calendar"""

    __tablename__ = "calendars"
    __filename__ = "calendar.txt"

    service_id = mapped_column(String, primary_key=True)
    monday = mapped_column(Integer)
    tuesday = mapped_column(Integer)
    wednesday = mapped_column(Integer)
    thursday = mapped_column(Integer)
    friday = mapped_column(Integer)
    saturday = mapped_column(Integer)
    sunday = mapped_column(Integer)
    start_date = mapped_column(String)
    end_date = mapped_column(String)

    calendar_dates = relationship(
        "CalendarDate", back_populates="calendar", passive_deletes=True
    )
    calendar_attributes = relationship(
        "CalendarAttribute", back_populates="calendar", passive_deletes=True
    )
    trips = relationship("Trip", back_populates="calendar", passive_deletes=True)

    @reconstructor
    def _init_on_load_(self) -> None:
        """Initialize the calendar object on load"""
        # pylint: disable=attribute-defined-outside-init

        self.start_datetime = pytz.timezone("America/New_York").localize(
            datetime.strptime(self.start_date, "%Y%m%d")
        )

        self.end_datetime = pytz.timezone("America/New_York").localize(
            datetime.strptime(self.end_date, "%Y%m%d")
        )

    def operates_on_date(self, date: datetime) -> bool:
        """Returns true if the calendar operates on the date

        Args:
            date (datetime): The date to check
        Returns:
            bool: True if the calendar operates on the date
        """
        exception = next(
            (s for s in self.calendar_dates if s.date == date.strftime("%Y%m%d")), None
        )

        return bool(
            self.start_datetime.date() <= date.date() <= self.end_datetime.date()
            and getattr(self, date.strftime("%A").lower())
            and not (exception and exception.exception_type == "2")
        ) or (exception and exception.exception_type == "1")
