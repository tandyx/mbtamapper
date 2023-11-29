"""File to hold the FacilityProperty class and its associated methods."""
from typing import override

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from .gtfs_base import GTFSBase


class FacilityProperty(GTFSBase):  # pylint: disable=too-few-public-methods
    """Facilities Properties"""

    __tablename__ = "facilities_properties"
    __filename__ = "facilities_properties.txt"

    facility_id = Column(
        String,
        ForeignKey("facilities.facility_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    property_id = Column(String, primary_key=True)
    value = Column(String, primary_key=True)

    facility = relationship("Facility", back_populates="facility_properties")

    @override
    def as_dict(self):
        """Return the facility property as a dictionary

        Returns:
            dict: facility property as a dictionary"""
        return {self.property_id: self.value}
