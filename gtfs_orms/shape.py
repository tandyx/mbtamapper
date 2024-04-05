"""File to hold the Shape class and its associated methods."""

from typing import TYPE_CHECKING

from geojson import Feature
from shapely.geometry import LineString
from sqlalchemy.orm import mapped_column, reconstructor, relationship, Mapped

from .gtfs_base import GTFSBase

if TYPE_CHECKING:
    from .shape_point import ShapePoint
    from .trip import Trip


class Shape(GTFSBase):
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
        """Return a shapely `LineString` object of the shape"""

        return LineString([sp.as_point() for sp in self.sorted_points])

    def as_feature(self, *include) -> Feature:  # pylint: disable=unused-argument
        """Returns shape object as a feature.

        args:
            - `*include`: A list of properties to include in the feature object.\n
        Returns:
            - `Feature`: A GeoJSON feature object.
        """

        feature = Feature(
            id=self.shape_id,
            geometry=self.as_linestring(),
            properties=self.trips[0].route.as_json(*include),
        )

        return feature
