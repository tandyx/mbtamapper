"""File to hold the CalendarAttribute class and its associated methods."""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .gtfs_base import GTFSBase


class CalendarAttribute(GTFSBase):  # pylint: disable=too-few-public-methods
    """Calendar Attributes"""

    __tablename__ = "calendar_attributes"
    __filename__ = "calendar_attributes.txt"

    service_id = Column(
        String,
        ForeignKey("calendars.service_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    service_description = Column(String)
    service_schedule_name = Column(String)
    service_schedule_type = Column(String)
    service_schedule_typicality = Column(String)
    rating_start_date = Column(String)
    rating_end_date = Column(String)
    rating_description = Column(String)

    calendar = relationship("Calendar", back_populates="calendar_attributes")
