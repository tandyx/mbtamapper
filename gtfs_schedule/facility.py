"""File to hold the Calendar class and its associated methods."""
from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, String, Float
from gtfs_loader.gtfs_base import GTFSBase


class Facility(GTFSBase):
    """Facilities"""

    __tablename__ = "facilities"

    facility_id = Column(String, primary_key=True)
    facility_code = Column(String)
    facility_class = Column(String)
    facility_type = Column(String)
    stop_id = Column(
        String,
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    facility_short_name = Column(String)
    facility_long_name = Column(String)
    facility_desc = Column(String)
    facility_lat = Column(Float)
    facility_lon = Column(Float)
    wheelchair_facility = Column(String)

    facility_properties = relationship(
        "FacilityProperty", back_populates="facility", passive_deletes=True
    )

    stop = relationship("Stop", back_populates="facilities")

    def __repr__(self) -> str:
        return f"<Facilities(facility_id={self.facility_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the facility"""
        return Point(self.facility_lon, self.facility_lat)

    def as_feature(self) -> Feature:
        """Returns facility object as a feature."""

        facility_dict = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["_sa_instance_state", "facility_properties"] and v
        } | {p.property_id: p.value for p in self.facility_properties}

        feature = Feature(
            id=self.facility_id,
            geometry=self.as_point(),
            properties=facility_dict,
        )

        return feature
