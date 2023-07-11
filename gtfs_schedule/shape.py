"""File to hold the Calendar class and its associated methods."""
import polyline
from shapely.geometry import LineString
from geojson import Feature

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, reconstructor

from gtfs_loader.gtfs_base import GTFSBase


class Shape(GTFSBase):
    """Shape"""

    __tablename__ = "shapes"

    shape_id = Column(String, primary_key=True, index=False)

    trips = relationship("Trip", back_populates="shape", passive_deletes=True)
    shape_points = relationship(
        "ShapePoint", back_populates="shape", passive_deletes=True
    )

    @reconstructor
    def init_on_load(self) -> None:
        """Load the shape points into a list of ShapePoint objects."""
        # pylint: disable=attribute-defined-outside-init

        self.sorted_points = sorted(
            self.shape_points, key=lambda x: x.shape_pt_sequence
        )

    def __repr__(self) -> str:
        return f"<Shape(shape_id={self.shape_id})>"

    def as_linestring(self) -> LineString:
        """Return a shapely LineString object of the shape"""

        return LineString([sp.as_point() for sp in self.sorted_points])

    def as_polyline(self) -> str:
        """Return a polyline string of the shape"""

        return polyline.encode([sp.as_tuple() for sp in self.sorted_points])

    def as_feature(self) -> Feature:
        """Returns shape object as a feature."""

        feature = Feature(
            id=self.shape_id,
            geometry=self.as_linestring(),
            properties=self.trips[0].route.as_dict(),
        )

        return feature
