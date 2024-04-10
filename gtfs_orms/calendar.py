"""File to hold the Calendar class and its associated methods."""

from datetime import datetime
from typing import TYPE_CHECKING

import pytz
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .calendar_attribute import CalendarAttribute
    from .calendar_date import CalendarDate
    from .trip import Trip


class Calendar(Base):
    """Calendar"""

    __tablename__ = "calendars"
    __filename__ = "calendar.txt"

    service_id: Mapped[str] = mapped_column(primary_key=True)
    monday: Mapped[int]
    tuesday: Mapped[int]
    wednesday: Mapped[int]
    thursday: Mapped[int]
    friday: Mapped[int]
    saturday: Mapped[int]
    sunday: Mapped[int]
    start_date: Mapped[str]
    end_date: Mapped[str]

    calendar_dates: Mapped[list["CalendarDate"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    calendar_attributes: Mapped[list["CalendarAttribute"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="calendar", passive_deletes=True
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
            - `date (datetime)`: The date to check
        Returns:
            - `bool`: True if the calendar operates on the date
        """
        exception = next(
            (s for s in self.calendar_dates if s.date == date.strftime("%Y%m%d")), None
        )

        return bool(
            self.start_datetime.date() <= date.date() <= self.end_datetime.date()
            and getattr(self, date.strftime("%A").lower())
            and not (exception and exception.exception_type == "2")
        ) or (exception and exception.exception_type == "1")

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
