"""File to hold the Calendar class and its associated methods."""
# pylint: disable=line-too-long
from sqlalchemy import Integer, ForeignKey, Column, String
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase
from helper_functions import format_time, to_seconds, lazy_convert


class StopTime(GTFSBase):
    """Stop Times"""

    __tablename__ = "stop_times"

    trip_id = Column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    arrival_time = Column(String)
    departure_time = Column(String)
    stop_id = Column(
        String, ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    stop_sequence = Column(Integer, primary_key=True)
    stop_headsign = Column(String)
    pickup_type = Column(String)
    drop_off_type = Column(String)
    timepoint = Column(String)
    checkpoint_id = Column(String)
    continuous_pickup = Column(String)
    continuous_drop_off = Column(String)

    stop = relationship("Stop", back_populates="stop_times")
    trip = relationship("Trip", back_populates="stop_times")

    @reconstructor
    def init_on_load(self):
        """Reconstructs the object on load from the database.
        executes after the object is loaded from the database and in init"""
        # pylint: disable=attribute-defined-outside-init
        self.destination_label = self.stop_headsign or self.trip.trip_headsign
        self.departure_seconds = to_seconds(self.departure_time)
        self.departure_datetime = lazy_convert(self.departure_time)

    def __repr__(self) -> str:
        return f"<StopTime(trip_id={self.trip_id}, stop_id={self.stop_id})>"

    def as_html(self) -> str:
        """Returns a StopTime obj as an html row"""

        return (
            f"""<tr> <td style='text-decoration:none;color:#{self.trip.route.route_color};'>{self.trip.route.route_short_name or self.trip.route.route_long_name}</td>"""
            f"""<td>{self.trip.trip_short_name or self.trip_id}</td>"""
            f"""<td>{self.destination_label}</td>"""
            f"""<td>{format_time(self.departure_time)}</td>"""
            f"""<td>{self.stop.platform_name}</td></tr>"""
        )
