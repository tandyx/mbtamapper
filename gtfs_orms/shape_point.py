"""File to hold the Calendar class and its associated methods."""

from typing import TYPE_CHECKING, Optional

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .shape import Shape


class ShapePoint(GTFSBase):
    """Shape"""

    __tablename__ = "shape_points"
    __filename__ = "shapes.txt"

    shape_id: str = mapped_column(
        String,
        ForeignKey("shapes.shape_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    shape_pt_lat: Optional[float] = mapped_column(Float)
    shape_pt_lon: Optional[float] = mapped_column(Float)
    shape_pt_sequence: Optional[int] = mapped_column(Integer, primary_key=True)
    shape_dist_traveled: Optional[float] = mapped_column(Float)

    shape: "Shape" = relationship("Shape", back_populates="shape_points")

    def as_point(self) -> Point:
        """Returns a shapely Point object of the shape point"""
        return Point(self.shape_pt_lon, self.shape_pt_lat)

    def as_feature(self, *include: str) -> Feature:
        """Returns shape point object as a feature.

        Args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: A GeoJSON feature object.
        """

        return Feature(
            id=self.shape_id,
            geometry=self.as_point(),
            properties=self.as_json(*include),
        )
