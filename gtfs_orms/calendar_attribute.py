"""File to hold the CalendarAttribute class and its associated methods."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .calendar import Calendar


class CalendarAttribute(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Attributes"""

    __tablename__ = "calendar_attributes"
    __filename__ = "calendar_attributes.txt"

    service_id: str = mapped_column(
        "service_id",
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    service_description: str = mapped_column("service_description", String)
    service_schedule_name: str = mapped_column("service_schedule_name", String)
    service_schedule_type: str = mapped_column("service_schedule_type", String)
    service_schedule_typicality: str = mapped_column(
        "service_schedule_typicality", String
    )
    rating_start_date: str = mapped_column("rating_start_date", String)
    rating_end_date: str = mapped_column("rating_end_date", String)
    rating_description: str = mapped_column("rating_description", String)

    calendar: "Calendar" = relationship(
        "Calendar", back_populates="calendar_attributes"
    )
