"""File to hold the Agency class and its associated methods."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .route import Route


class Agency(GTFSBase):
    """Agency"""

    __tablename__ = "agencies"
    __filename__ = "agency.txt"

    agency_id: str = mapped_column(String, primary_key=True)
    agency_name: str = mapped_column(String)
    agency_url: str = mapped_column(String)
    agency_timezone: str = mapped_column(String)
    agency_lang: str = mapped_column(String)
    agency_phone: str = mapped_column(String)

    routes: list["Route"] = relationship(
        "Route", back_populates="agency", passive_deletes=True
    )

    def as_html(self) -> str:
        """Return the agency as HTML

        Returns:
            str: agency as HTML"""
        return (
            f"<a href = {self.agency_url} target='_blank'>"
            f"{self.agency_name}</a> ({self.agency_phone})"
        )
