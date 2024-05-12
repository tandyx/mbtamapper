"""File to hold the CalendarAttribute class and its associated methods."""

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .calendar import Calendar


class CalendarAttribute(Base):  # pylint: disable=too-few-public-methods
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
    rating_start_date: Mapped[Optional[dt.datetime]]
    rating_end_date: Mapped[Optional[dt.datetime]]
    rating_description: Mapped[Optional[str]]

    calendar: Mapped["Calendar"] = relationship(back_populates="calendar_attributes")

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")
