"""File to hold the Calendar class and its associated methods."""

from datetime import datetime
from typing import TYPE_CHECKING

import pytz
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .calendar_attribute import CalendarAttribute
    from .calendar_date import CalendarDate
    from .trip import Trip


class Calendar(GTFSBase):
    """Calendar"""

    __tablename__ = "calendars"
    __filename__ = "calendar.txt"

    service_id: str = mapped_column("service_id", String, primary_key=True)
    monday: int = mapped_column("monday", Integer)
    tuesday: int = mapped_column("tuesday", Integer)
    wednesday: int = mapped_column("wednesday", Integer)
    thursday: int = mapped_column("thursday", Integer)
    friday: int = mapped_column("friday", Integer)
    saturday: int = mapped_column("saturday", Integer)
    sunday: int = mapped_column("sunday", Integer)
    start_date: str = mapped_column("start_date", String)
    end_date: str = mapped_column("end_date", String)

    calendar_dates: list["CalendarDate"] = relationship(
        "CalendarDate", back_populates="calendar", passive_deletes=True
    )
    calendar_attributes: list["CalendarAttribute"] = relationship(
        "CalendarAttribute", back_populates="calendar", passive_deletes=True
    )
    trips: list["Trip"] = relationship(
        "Trip", back_populates="calendar", passive_deletes=True
    )

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
