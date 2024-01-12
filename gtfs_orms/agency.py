"""File to hold the Agency class and its associated methods."""
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase


class Agency(GTFSBase):
    """Agency"""

    __tablename__ = "agencies"
    __filename__ = "agency.txt"

    agency_id = mapped_column(String, primary_key=True)
    agency_name = mapped_column(String)
    agency_url = mapped_column(String)
    agency_timezone = mapped_column(String)
    agency_lang = mapped_column(String)
    agency_phone = mapped_column(String)

    routes = relationship("Route", back_populates="agency", passive_deletes=True)

    def as_html(self) -> str:
        """Return the agency as HTML

        Returns:
            str: agency as HTML"""
        return (
            f"<a href = {self.agency_url} target='_blank'>"
            f"{self.agency_name}</a> ({self.agency_phone})"
        )
