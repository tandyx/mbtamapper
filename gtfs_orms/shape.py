"""File to hold the Shape class and its associated methods."""

import time
from typing import TYPE_CHECKING, override

from geojson import Feature
from shapely.geometry import LineString
from sqlalchemy.orm import Mapped, mapped_column, reconstructor, relationship

from .base import Base

if TYPE_CHECKING:
    from .shape_point import ShapePoint
    from .trip import Trip


class Shape(Base):
    """Shape"""

    __tablename__ = "shapes"

    shape_id: Mapped[str] = mapped_column(primary_key=True)

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="shape", passive_deletes=True
    )
    shape_points: Mapped[list["ShapePoint"]] = relationship(
        back_populates="shape", passive_deletes=True
    )

    @reconstructor
    def _init_on_load_(self) -> None:
        """Load the shape points into a list of ShapePoint objects."""
        # pylint: disable=attribute-defined-outside-init

        self.sorted_points: list["ShapePoint"] = sorted(
            self.shape_points, key=lambda x: x.shape_pt_sequence
        )

    def as_linestring(self) -> LineString:
        """Return a shapely `LineString` object of the shape

        returns:
            - `LineString`: A shapely LineString object.
        """

        return LineString([sp.as_point() for sp in self.sorted_points])

    @override
    def as_feature(self, *include: str) -> Feature:  # pylint: disable=unused-argument
        """Returns shape object as a feature.

        args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: A GeoJSON feature object.
        """

        feature = Feature(
            id=self.shape_id,
            geometry=self.as_linestring(),
            properties=self.trips[0].route.as_json(*include)
            | {
                "timestamp": time.time(),
            },
        )

        return feature
