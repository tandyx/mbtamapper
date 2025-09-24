"""File to hold the Calendar class and its associated methods."""

import typing as t

from geojson import Feature
from shapely.geometry import Point
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .shape import Shape


class ShapePoint(Base):
    """Shape

    represents one point in a shape/line

    most of the property data is kinda useless, so it comes from the route instead.

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#shapestxt

    """

    __tablename__ = "shape_point"
    __filename__ = "shapes.txt"

    shape_id: Mapped[str] = mapped_column(
        ForeignKey("shape.shape_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    shape_pt_lat: Mapped[float]
    shape_pt_lon: Mapped[float]
    shape_pt_sequence: Mapped[int] = mapped_column(primary_key=True)
    shape_dist_traveled: Mapped[t.Optional[float]]

    shape: Mapped["Shape"] = relationship(back_populates="shape_points")

    def as_point(self) -> Point:
        """Returns a shapely Point object of the shape point

        returns:
            Point: A shapely Point object.
        """
        return Point(self.shape_pt_lon, self.shape_pt_lat)

    def as_feature(self, *include: str) -> Feature:
        """Returns shape point object as a feature.

        Args:
            include: A list of properties to include in the feature object.\n
        Returns:
            Feature: A GeoJSON feature object.
        """

        return Feature(
            id=self.shape_id,
            geometry=self.as_point(),
            properties=self.as_json(*include)
            | self.shape.trips[0].route.as_json(*include),
        )
