"""File to hold the CalendarDate class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..helper_functions import SQLA_GTFS_DATE
from .base import Base

if t.TYPE_CHECKING:
    from .calendar import Calendar


class CalendarDate(Base):  # pylint: disable=too-few-public-methods
    """CalendarDate

    typically represents holidays or exceptions to the normal schedule.

    - `exception_type = 1` service operates on `CalendarDate.date` (ADDED)
    - `exception_type = 2` service doesn't operate on `CalendarDate.date` (REMOVED)

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#calendar_datestxt

    """

    __tablename__ = "calendar_date"
    __filename__ = "calendar_dates.txt"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("calendar.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    date: Mapped[dt.datetime] = mapped_column(SQLA_GTFS_DATE, primary_key=True)
    exception_type: Mapped[str]
    holiday_name: Mapped[t.Optional[str]]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_dates")
