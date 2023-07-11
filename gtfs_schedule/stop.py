"""File to hold the Calendar class and its associated methods."""
from shapely.geometry import Point
from geojson import Feature

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Float, ForeignKey
from gtfs_loader.gtfs_base import GTFSBase


class Stop(GTFSBase):
    """Stop"""

    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True)
    stop_code = Column(String)
    stop_name = Column(String)
    stop_desc = Column(String)
    platform_code = Column(String)
    platform_name = Column(String)
    stop_lat = Column(Float)
    stop_lon = Column(Float)
    zone_id = Column(String)
    stop_address = Column(String)
    stop_url = Column(String)
    level_id = Column(String)
    location_type = Column(String)
    parent_station = Column(String, ForeignKey("stops.stop_id"))
    wheelchair_boarding = Column(String)
    municipality = Column(String)
    on_street = Column(String)
    at_street = Column(String)
    vehicle_type = Column(String)

    stop_times = relationship("StopTime", back_populates="stop", passive_deletes=True)
    to_stop_transfers = relationship(
        "Transfer",
        back_populates="to_stop",
        foreign_keys="Transfer.to_stop_id",
        passive_deletes=True,
    )
    from_stop_transfers = relationship(
        "Transfer",
        back_populates="from_stop",
        foreign_keys="Transfer.from_stop_id",
        passive_deletes=True,
    )
    facilities = relationship("Facility", back_populates="stop", passive_deletes=True)

    parent_stop = relationship(
        "Stop", primaryjoin="foreign(Stop.parent_station)==remote(Stop.stop_id)"
    )

    exclude_keys = [
        "_sa_instance_state",
        "parent_station",
        "stop_times",
        "facilities",
        "parent_stop",
    ]

    def __repr__(self):
        return f"<Stop(stop_id={self.stop_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the stop"""
        return Point(self.stop_lon, self.stop_lat)

    def as_feature(self) -> Feature:
        """Returns stop object as a feature."""

        properties = {
            k: v
            for k, v in self.__dict__.items()
            if v and k not in Stop.exclude_keys + ["stop_lat", "stop_lon"]
        }

        dest_labels = {
            st.destination_label
            for st in self.stop_times
            if st.trip.is_added and not st.is_destination()
        }
        if dest_labels:
            properties.update({"board_here_for": ", ".join(dest_labels)})

        feature = Feature(
            id=self.stop_id, geometry=self.as_point(), properties=properties
        )

        return feature

    def to_lookup_dict(self) -> dict[str]:
        """Returns a dictionary of the stop object for use in a lookup table."""
        return {
            "PartitionKey": self.parent_station,
            "RowKey": self.platform_code or "Unassigned",
        } | {
            k: v
            for k, v in self.__dict__.items()
            if v and k not in Stop.exclude_keys + ["platform_code", "parent_station"]
        }
