"""File to hold the FacilityProperty class and its associated methods."""

from typing import TYPE_CHECKING, override

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .facility import Facility


class FacilityProperty(GTFSBase):  # pylint: disable=too-few-public-methods
    """Facilities Properties"""

    __tablename__ = "facilities_properties"
    __filename__ = "facilities_properties.txt"

    facility_id: str = mapped_column(
        "facility_id",
        String,
        ForeignKey("facilities.facility_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    property_id: str = mapped_column("property_id", String, primary_key=True)
    value: str = mapped_column("value", String, primary_key=True)

    facility: "Facility" = relationship(
        "Facility", back_populates="facility_properties"
    )

    @override
    def as_dict(self, *args, **kwargs):
        """Return the facility property as a dictionary \
        (useful for JSON serialization).
        
        This method is an override of the as_dict method, and args, kwargs are unused.
            
        Returns:
            `dict`: facility property as a dictionary as {property_id: value}"""
        return {self.property_id: self.value}
