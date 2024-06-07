"""File to hold the Facility class and its associated methods."""

import typing as t

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .facility_property import FacilityProperty
    from .stop import Stop


class Facility(Base):
    """Facility
    
    this class is the child of the `Stop` table.
    
    holds many different types of facilities, \
        such as bike racks, parking, elevators, etc.
        
    for now, only `facility_type` = `"bike-parking"` and `"parking-area"` aren't purged.
    
    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#facilitiestxt
    
    """

    __tablename__ = "facilities"
    __filename__ = "facilities.txt"

    facility_id: Mapped[str] = mapped_column(primary_key=True)
    facility_code: Mapped[t.Optional[str]]
    facility_class: Mapped[t.Optional[str]]
    facility_type: Mapped[t.Optional[str]]
    stop_id: Mapped[t.Optional[str]] = mapped_column(
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    facility_short_name: Mapped[t.Optional[str]]
    facility_long_name: Mapped[t.Optional[str]]
    facility_desc: Mapped[t.Optional[str]]
    facility_lat: Mapped[t.Optional[float]]
    facility_lon: Mapped[t.Optional[float]]
    wheelchair_facility: Mapped[t.Optional[str]]

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

    @t.override
    def as_json(self, *include, **kwargs) -> dict[str, t.Any]:
        """Returns facility object as a dictionary.\
            same as `as_dict` but with the facility properties included.
        
        args:
            - `*include`: A list of properties to include in the dictionary.
            - `**kwargs`: unused\n
        Returns:
            - `dict[str, Any]`: facility as a dictionary.\n
        """

        return super().as_json(*include, **kwargs) | {
            fp.property_id: fp.value for fp in self.facility_properties
        }

    def as_feature(self, *include: str) -> Feature:
        """Returns facility object as a feature.

        args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: facility as a feature.\n
        """

        if (point := self.as_point()) == self.stop.as_point():
            point = Point(self.facility_lon + 0.003, self.facility_lat + 0.003)
        return Feature(
            id=self.facility_id, geometry=point, properties=self.as_json(*include)
        )
