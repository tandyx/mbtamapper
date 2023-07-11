"""File to hold the Calendar class and its associated methods."""
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, String
from gtfs_loader.gtfs_base import GTFSBase


class FacilityProperty(GTFSBase):
    """Facilities Properties"""

    __tablename__ = "facilities_properties"

    facility_id = Column(
        String,
        ForeignKey("facilities.facility_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    property_id = Column(String, primary_key=True)
    value = Column(String, primary_key=True)

    facility = relationship("Facility", back_populates="facility_properties")

    def __repr__(self) -> str:
        return f"<FacilityProperty(facility_id={self.facility_id}, property_id={self.property_id})>"
