"""File to hold the Shape class and its associated methods."""

import time
import typing as t

from geojson import Feature
from shapely.geometry import LineString
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if t.TYPE_CHECKING:
    from .shape_point import ShapePoint
    from .trip import Trip


class Shape(Base):
    """Shape

    this table isn't in the gtfs spec, but is used to \
        group `ShapePoint`s together

    """

    __tablename__ = "shape"

    shape_id: Mapped[str] = mapped_column(primary_key=True)

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="shape", passive_deletes=True
    )
    shape_points: Mapped[list["ShapePoint"]] = relationship(
        back_populates="shape",
        passive_deletes=True,
        order_by="ShapePoint.shape_pt_sequence",
    )

    cache: dict[str, LineString] = {}

    def as_linestring(self, use_cache=False) -> LineString:
        """Return a shapely `LineString` object of the shape

        Args:
            use_cache (boolean): use a cache to return this linestring default False

        Returns:
            LineString: A shapely LineString object.
        """

        def _gen_ls():
            return LineString([sp.as_point() for sp in sorted(self.shape_points)])

        if not use_cache:
            return _gen_ls()

        if self.shape_id in self.__class__.cache:
            return self.__class__.cache[self.shape_id]
        self.__class__.cache[self.shape_id] = (linestr := _gen_ls())
        return linestr

    def as_feature(self, *include: str) -> Feature:
        """Returns shape object as a feature.

        Args:
            include: A list of properties to include in the feature object.\n
        Returns:
            Feature: A GeoJSON feature object.
        """

        return Feature(
            id=self.shape_id,
            geometry=self.as_linestring(),
            properties=(
                self.as_json(*include)
                | ({"timestamp": time.time()} if "timestamp" in include else {})
            ),
        )

    @t.override
    def as_json(self, *include, **kwargs) -> dict[str, t.Any]:
        """Returns shape object as a dictionary.

        Args:
            include: A list of properties to include in the dictionary.
            kwargs: unused\n
        Returns:
            dict[str, Any]: shape as a dictionary.\n
        """

        return super().as_json(*include, **kwargs) | self.trips[0].route.as_json(
            *include
        )
