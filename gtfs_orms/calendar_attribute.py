"""File to hold the CalendarAttribute class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .calendar import Calendar


class CalendarAttribute(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Attributes"""

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
    rating_start_date: Mapped[Optional[str]]
    rating_end_date: Mapped[Optional[str]]
    rating_description: Mapped[Optional[str]]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_attributes")
