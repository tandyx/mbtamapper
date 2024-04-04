"""File to hold the Facility class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .facility_property import FacilityProperty
    from .stop import Stop

# pylint: disable=line-too-long


class Facility(GTFSBase):
    """Facilities"""

    __tablename__ = "facilities"
    __filename__ = "facilities.txt"

    facility_id: str = mapped_column("facility_id", String, primary_key=True)
    facility_code: Optional[str] = mapped_column("facility_code", String)
    facility_class: Optional[str] = mapped_column("facility_class", String)
    facility_type: Optional[str] = mapped_column("facility_type", String)
    stop_id: Optional[str] = mapped_column(
        "stop_id",
        String,
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    facility_short_name: Optional[str] = mapped_column("facility_short_name", String)
    facility_long_name: Optional[str] = mapped_column("facility_long_name", String)
    facility_desc: Optional[str] = mapped_column("facility_desc", String)
    facility_lat: Optional[float] = mapped_column("facility_lat", Float)
    facility_lon: Optional[float] = mapped_column("facility_lon", Float)
    wheelchair_facility: Optional[str] = mapped_column("wheelchair_facility", String)

    facility_properties: list["FacilityProperty"] = relationship(
        "FacilityProperty", back_populates="facility", passive_deletes=True
    )

    stop: "Stop" = relationship("Stop", back_populates="facilities")

    def as_point(self) -> Point:
        """Returns a shapely Point object of the facility

        Returns:
            - `Point`: shapely Point object of the facility
        """
        return Point(self.facility_lon, self.facility_lat)

    def as_feature(self) -> Feature:
        """Returns facility object as a feature.

        Returns:
            - `Feature`: facility as a feature.\n
        """

        point = self.as_point()
        if point == self.stop.as_point():
            point = Point(self.facility_lon + 0.001, self.facility_lat + 0.001)

        return Feature(id=self.facility_id, geometry=point, properties=self.as_json())
