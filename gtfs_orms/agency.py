"""File to hold the Agency class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .route import Route


class Agency(GTFSBase):
    """Agency"""

    __tablename__ = "agencies"
    __filename__ = "agency.txt"

    agency_id: str = mapped_column("agency_id", String, primary_key=True)
    agency_name: Optional[str] = mapped_column("agency_name", String)
    agency_url: Optional[str] = mapped_column("agency_url", String)
    agency_timezone: Optional[str] = mapped_column("agency_timezone", String)
    agency_lang: Optional[str] = mapped_column("agency_lang", String)
    agency_phone: Optional[str] = mapped_column("agency_phone", String)

    routes: list["Route"] = relationship(
        "Route", back_populates="agency", passive_deletes=True
    )
