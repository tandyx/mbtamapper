"""File to hold the Shape class and its associated methods."""
from geojson import Feature
from shapely.geometry import LineString
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from .gtfs_base import GTFSBase


class Shape(GTFSBase):
    """Shape"""

    __tablename__ = "shapes"

    shape_id = mapped_column(String, primary_key=True, index=False)

    trips = relationship("Trip", back_populates="shape", passive_deletes=True)
    shape_points = relationship(
        "ShapePoint", back_populates="shape", passive_deletes=True
    )

    @reconstructor
    def _init_on_load_(self) -> None:
        """Load the shape points into a list of ShapePoint objects."""
        # pylint: disable=attribute-defined-outside-init

        self.sorted_points = sorted(
            self.shape_points, key=lambda x: x.shape_pt_sequence
        )

    def as_linestring(self) -> LineString:
        """Return a shapely LineString object of the shape"""

        return LineString([sp.as_point() for sp in self.sorted_points])

    def as_feature(self) -> Feature:
        """Returns shape object as a feature."""

        feature = Feature(
            id=self.shape_id,
            geometry=self.as_linestring(),
            properties=self.trips[0].route.as_html_dict(),
        )

        return feature
