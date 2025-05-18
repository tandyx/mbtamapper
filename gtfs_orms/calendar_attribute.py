"""File to hold the CalendarAttribute class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helper_functions import SQLA_GTFS_DATE

from .base import Base

if t.TYPE_CHECKING:
    from .calendar import Calendar


class CalendarAttribute(Base):
    """CalendarAttribute
    
    details extra information about a `Calendar`, \
        but only used to purge cannonical trips as of rn
        
    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#calendar_attributestxt
    
    """

    __tablename__ = "calendar_attributes"
    __filename__ = "calendar_attributes.txt"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    service_description: Mapped[str]
    service_schedule_name: Mapped[str]
    service_schedule_type: Mapped[str]
    service_schedule_typicality: Mapped[str]
    rating_start_date: Mapped[dt.datetime] = mapped_column(SQLA_GTFS_DATE)
    rating_end_date: Mapped[t.Optional[dt.datetime]]
    rating_description: Mapped[str]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_attributes")
