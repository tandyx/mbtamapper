"""Facility Property Definition"""
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String
from gtfs_loader.gtfs_base import GTFSBase


class FacilityPropertyDefintion(GTFSBase):
    """Facilities Properties"""

    __tablename__ = "facilities_properties_defintions"

    property_id = Column(String, primary_key=True)
    definition = Column(String)
    possible_values = Column(String)

    facility_properties = relationship(
        "FacilityProperty",
        back_populates="facility_property_defintion",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<FacilityPropertyDefintion(property_id={self.property_id})>"

    def __str__(self) -> str:
        return self.__repr__()
