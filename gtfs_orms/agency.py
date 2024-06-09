"""File to hold the Agency class and its associated methods."""

import typing as t

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .route import Route


class Agency(Base):
    """Agency

    holds information about agancies within the system

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#agencytxt

    """

    __tablename__ = "agencies"
    __filename__ = "agency.txt"

    agency_id: Mapped[str] = mapped_column(primary_key=True)
    agency_name: Mapped[str]
    agency_url: Mapped[str]
    agency_timezone: Mapped[str]
    agency_lang: Mapped[str]
    agency_phone: Mapped[str]

    routes: Mapped[list["Route"]] = relationship(
        back_populates="agency", passive_deletes=True
    )
