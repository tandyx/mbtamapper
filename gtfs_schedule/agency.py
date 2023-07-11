"""Agency"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String
from gtfs_loader.gtfs_base import GTFSBase


class Agency(GTFSBase):
    """Agency"""

    __tablename__ = "agencies"

    agency_id = Column(String, primary_key=True)
    agency_name = Column(String)
    agency_url = Column(String)
    agency_timezone = Column(String)
    agency_lang = Column(String)
    agency_phone = Column(String)

    routes = relationship("Route", back_populates="agency", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Agency(agency_id={self.agency_id})>"
