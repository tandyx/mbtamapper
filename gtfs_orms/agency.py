"""File to hold the Agency class and its associated methods."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .route import Route


class Agency(GTFSBase):
    """Agency"""

    __tablename__ = "agencies"
    __filename__ = "agency.txt"

    agency_id: Mapped[str] = mapped_column(primary_key=True)
    agency_name: Mapped[str]
    agency_url: Mapped[str]
    agency_timezone: Mapped[str]
    agency_lang: Mapped[str]
    agency_phone: Mapped[str]

    routes: Mapped[list["Route"]] = relationship(
        "Route", back_populates="agency", passive_deletes=True
    )
