"""File to hold the StopTime class and its associated methods."""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, reconstructor, relationship

from helper_functions import *

from .gtfs_base import GTFSBase


class StopTime(GTFSBase):
    """Stop Times"""

    __tablename__ = "stop_times"
    __filename__ = "stop_times.txt"

    trip_id = mapped_column(
        String,
        ForeignKey("trips.trip_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    arrival_time = mapped_column(String)
    departure_time = mapped_column(String)
    stop_id = mapped_column(
        String, ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    stop_sequence = mapped_column(Integer, primary_key=True)
    stop_headsign = mapped_column(String)
    pickup_type = mapped_column(String)
    drop_off_type = mapped_column(String)
    timepoint = mapped_column(String)
    checkpoint_id = mapped_column(String)
    continuous_pickup = mapped_column(String)
    continuous_drop_off = mapped_column(String)

    stop = relationship("Stop", back_populates="stop_times")
    trip = relationship("Trip", back_populates="stop_times")

    @reconstructor
    def _init_on_load_(self):
        """Reconstructs the object on load from the database.
        executes after the object is loaded from the database and in init"""
        # pylint: disable=attribute-defined-outside-init
        self.destination_label = self.stop_headsign or self.trip.trip_headsign
        self.departure_seconds = to_seconds(self.departure_time)
        self.arrival_seconds = to_seconds(self.arrival_time)
        self.departure_datetime = lazy_convert(self.departure_time)
        self.unix_departure_time = self.departure_seconds + get_date().timestamp()
        self.unix_arrival_time = self.arrival_seconds + get_date().timestamp()

    def is_flag_stop(self) -> bool:
        """Returns true if this StopTime is a flag stop"""
        return self.trip.route.route_type == "2" and (
            self.pickup_type == "3" or self.drop_off_type == "3"
        )

    def is_early_departure(self) -> bool:
        """Returns true if this StopTime is an early departure stop"""
        return (
            self.trip.route.route_type == "2"
            and self.timepoint == "0"
            and not self.is_destination()
        )

    def is_active(self, date: datetime) -> bool:
        """Returns true if this StopTime is active on the given date and time"""

        return self.trip.calendar.operates_on_date(date) and self.departure_seconds > (
            get_current_time().timestamp() - get_date().timestamp()
        )

    def is_destination(self) -> bool:
        """Returns true if this StopTime is the last stop in the trip"""
        return self.stop_sequence == max(
            st.stop_sequence for st in self.trip.stop_times
        )

    def as_html(self) -> str:
        """Returns a StopTime obj as an html row"""

        trip_name = self.trip.trip_short_name or self.trip_id

        flag_stop = (
            "<div class = 'tooltip'>"
            f"<span class='flag_stop'>{trip_name}</span>"
            "<span class='tooltiptext'>Flag stop.</span></div>"
            if self.is_flag_stop()
            else ""
        )

        early_departure = (
            "<div class = 'tooltip'>"
            f"<span class='early_departure'>{trip_name}</span>"
            "<span class='tooltiptext'>Early departure stop.</span></div>"
            if self.is_early_departure()
            else ""
        )

        return (
            f"""<tr> <td style='color:#{self.trip.route.route_color};'>"""
            f"""{shorten(self.trip.route.route_short_name or self.trip.route.route_long_name)}</td>"""  # pylint: disable=line-too-long
            f"""<td>{flag_stop or early_departure or trip_name}</td>"""
            f"""<td>{self.destination_label}</td>"""
            f"""<td>{format_time(self.departure_time)}</td>"""
            f"""<td>{self.stop.platform_name or ""}</td></tr>"""
        )
