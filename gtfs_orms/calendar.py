"""File to hold the Calendar class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    start_date: Mapped[dt.datetime]
    end_date: Mapped[dt.datetime]

    calendar_dates: Mapped[list["CalendarDate"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    calendar_attributes: Mapped[list["CalendarAttribute"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="calendar", passive_deletes=True
    )

    def operates_on(self, date: dt.datetime | dt.date) -> bool:
        """Returns true if the calendar operates on the date

        Args:
            - `date (datetime|date|str)`: The date to check\n
        Returns:
            - `bool`: True if the calendar operates on the date
        """

        if isinstance(date, dt.datetime):
            date: dt.date = date.date()
        exception = next((s for s in self.calendar_dates if s.date == date), None)
        return bool(
            self.start_date.date() <= date <= self.end_date.date()
            and getattr(self, date.strftime("%A").lower())
            and not (exception and exception.exception_type == "2")
        ) or (exception and exception.exception_type == "1")
