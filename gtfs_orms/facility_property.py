"""File to hold the FacilityProperty class and its associated methods."""

import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .facility import Facility


class FacilityProperty(Base):  # pylint: disable=too-few-public-methods
    """Facilitiy Properties

    this is an experimental table that holds additional facility attars

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#facilities_propertiestxt

    """

    __tablename__ = "facilities_properties"
    __filename__ = "facilities_properties.txt"

    facility_id: Mapped[str] = mapped_column(
        ForeignKey("facilities.facility_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    property_id: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(primary_key=True)

    facility: Mapped["Facility"] = relationship(back_populates="facility_properties")

    @t.override
    def as_dict(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Return the facility property as a dictionary \
        (useful for JSON serialization).
        
        This method is an override of the as_dict method, and args, kwargs are unused.
            
        Returns:
            `dict`: facility property as a dictionary as {property_id: value}"""
        return {self.property_id: self.value}
