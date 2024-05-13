"""File to hold the CalendarDate class and its associated methods."""

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .calendar import Calendar


class CalendarDate(Base):  # pylint: disable=too-few-public-methods
    """Calendar Dates

    typically represents holidays or exceptions to the normal schedule.

    - `exception_type = 1` service operates on `date`.
    - `exception_type = 2` service doesn't operate on `date`.
    """

    __tablename__ = "calendar_dates"
    __filename__ = "calendar_dates.txt"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[dt.datetime] = mapped_column(primary_key=True)
    exception_type: Mapped[Optional[str]]
    holiday_name: Mapped[Optional[str]]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_dates")
