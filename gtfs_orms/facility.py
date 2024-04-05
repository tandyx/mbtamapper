"""File to hold the Facility class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .facility_property import FacilityProperty
    from .stop import Stop

# pylint: disable=line-too-long


class Facility(GTFSBase):
    """Facilities"""

    __tablename__ = "facilities"
    __filename__ = "facilities.txt"

    facility_id: Mapped[str] = mapped_column(primary_key=True)
    facility_code: Mapped[Optional[str]]
    facility_class: Mapped[Optional[str]]
    facility_type: Mapped[Optional[str]]
    stop_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    facility_short_name: Mapped[Optional[str]]
    facility_long_name: Mapped[Optional[str]]
    facility_desc: Mapped[Optional[str]]
    facility_lat: Mapped[Optional[float]]
    facility_lon: Mapped[Optional[float]]
    wheelchair_facility: Mapped[Optional[str]]

    facility_properties: Mapped[list["FacilityProperty"]] = relationship(
        back_populates="facility", passive_deletes=True
    )

    stop: Mapped["Stop"] = relationship(back_populates="facilities")

    def as_point(self) -> Point:
        """Returns a shapely Point object of the facility

        Returns:
            - `Point`: shapely Point object of the facility
        """
        return Point(self.facility_lon, self.facility_lat)

    def as_feature(self, *include) -> Feature:
        """Returns facility object as a feature.

        args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: facility as a feature.\n
        """

        point = self.as_point()
        if point == self.stop.as_point():
            point = Point(self.facility_lon + 0.002, self.facility_lat + 0.002)
        return Feature(
            id=self.facility_id,
            geometry=point,
            properties=self.as_json(*include)
            | {
                k: v for fp in self.facility_properties for k, v in fp.as_dict().items()
            },
        )
