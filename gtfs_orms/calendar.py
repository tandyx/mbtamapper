"""File to hold the Calendar class and its associated methods."""

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from helper_functions import dt_from_str

from .base import Base

if TYPE_CHECKING:
    from .calendar_attribute import CalendarAttribute
    from .calendar_date import CalendarDate
    from .trip import Trip


class Calendar(Base):
    """Calendar

    represents when a service operates

    """

    __tablename__ = "calendars"
    __filename__ = "calendar.txt"

    service_id: Mapped[str] = mapped_column(primary_key=True)
    monday: Mapped[bool]
    tuesday: Mapped[bool]
    wednesday: Mapped[bool]
    thursday: Mapped[bool]
    friday: Mapped[bool]
    saturday: Mapped[bool]
    sunday: Mapped[bool]
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
        self.start_datetime = dt_from_str(self.start_date)
        self.end_datetime = dt_from_str(self.end_date)

    def operates_on(self, date: dt.datetime | dt.date | str, **kwargs) -> bool:
        """Returns true if the calendar operates on the date

        Args:
            - `date (datetime|date|str)`: The date to check;\\
                if `str` formated `YYYYMMDD`, but format can be changed\
                    with `strf` kwarg
            - `**kwargs`: Additional keyword arguments to pass to `dt_from_str` if date is str \n
        Returns:
            - `bool`: True if the calendar operates on the date
        """

        if isinstance(date, dt.datetime):
            date: dt.date = date.date()
        if isinstance(date, str):
            date = dt_from_str(date, **kwargs).date()
        exception = next(
            (s for s in self.calendar_dates if s.date == date.strftime("%Y%m%d")), None
        )
        return bool(
            self.start_datetime.date() <= date <= self.end_datetime.date()
            and getattr(self, date.strftime("%A").lower())
            and not (exception and exception.exception_type == "2")
        ) or (exception and exception.exception_type == "1")

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
