"""File to hold the Calendar class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..helper_functions import SQLA_GTFS_DATE, get_date
from .base import Base

if t.TYPE_CHECKING:
    from .calendar_attribute import CalendarAttribute
    from .calendar_date import CalendarDate
    from .trip import Trip


class Calendar(Base):
    """Calendar

    represents when a service operates

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#calendartxt

    """

    __tablename__ = "calendar"
    __filename__ = "calendar.txt"

    service_id: Mapped[str] = mapped_column(primary_key=True)
    monday: Mapped[bool]
    tuesday: Mapped[bool]
    wednesday: Mapped[bool]
    thursday: Mapped[bool]
    friday: Mapped[bool]
    saturday: Mapped[bool]
    sunday: Mapped[bool]
    start_date: Mapped[dt.datetime] = mapped_column(SQLA_GTFS_DATE)
    end_date: Mapped[dt.datetime] = mapped_column(SQLA_GTFS_DATE)

    calendar_dates: Mapped[list["CalendarDate"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    calendar_attributes: Mapped[list["CalendarAttribute"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )

    def is_active(self, _date: dt.datetime | dt.date | None = None, **kwargs) -> bool:
        """returns true if the calendar is active on the date

        wrapper for `operates_on`

        args:
            _date (datetime|date|str): The date to check, defaults to today \n
            kwargs: additional arguments passed to `get_date` \n
        returns:
            bool: True if the calendar is active on the date
        """

        return self.operates_on(_date or get_date(**kwargs))

    def operates_on(self, _date: dt.datetime | dt.date) -> bool:
        """Returns true if the calendar operates on the date

        Args:
            date (datetime|date|str): The date to check\n
        Returns:
            bool: True if the calendar operates on the date
        """

        if isinstance(_date, dt.datetime):
            _date: dt.date = _date.date()
        exception = next((s for s in self.calendar_dates if s.date == _date), None)
        return bool(
            self.start_date.date() <= _date <= self.end_date.date()
            and getattr(self, _date.strftime("%A").lower())
            and not (exception and exception.exception_type == "2")
        ) or (exception and exception.exception_type == "1")

    @property
    def active(self) -> bool:
        """wrapper for self.is_active"""
        return self.is_active(get_date())
