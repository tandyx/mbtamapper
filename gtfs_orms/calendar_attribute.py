"""File to hold the CalendarAttribute class and its associated methods."""

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
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
    service_description: Mapped[Optional[str]]
    service_schedule_name: Mapped[Optional[str]]
    service_schedule_type: Mapped[Optional[str]]
    service_schedule_typicality: Mapped[Optional[str]]
    rating_start_date: Mapped[Optional[dt.datetime]]
    rating_end_date: Mapped[Optional[dt.datetime]]
    rating_description: Mapped[Optional[str]]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_attributes")
