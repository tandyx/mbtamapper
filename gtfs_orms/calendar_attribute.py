"""File to hold the CalendarAttribute class and its associated methods."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase


class CalendarAttribute(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Attributes"""

    __tablename__ = "calendar_attributes"
    __filename__ = "calendar_attributes.txt"

    service_id = mapped_column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    service_description = mapped_column(String)
    service_schedule_name = mapped_column(String)
    service_schedule_type = mapped_column(String)
    service_schedule_typicality = mapped_column(String)
    rating_start_date = mapped_column(String)
    rating_end_date = mapped_column(String)
    rating_description = mapped_column(String)

    calendar = relationship("Calendar", back_populates="calendar_attributes")
