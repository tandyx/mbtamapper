"""File to hold the Prediction class and its associated methods."""
# pylint: disable=line-too-long
from datetime import datetime

from dateutil.parser import isoparse
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import reconstructor, relationship

from .gtfs_base import GTFSBase


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"

    prediction_id = Column(String)
    arrival_time = Column(String)
    departure_time = Column(String)
    direction_id = Column(String)
    schedule_relationship = Column(String)
    stop_sequence = Column(Integer)
    route_id = Column(String)
    stop_id = Column(String)
    trip_id = Column(String)
    vehicle_id = Column(String)
    index = Column(Integer, primary_key=True)

    route = relationship(
        "Route",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.route_id)==Route.route_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.stop_id)==Stop.stop_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    vehicle = relationship(
        "Vehicle",
        back_populates="predictions",
        primaryjoin="foreign(Prediction.vehicle_id)==Vehicle.vehicle_id",
        viewonly=True,
    )

    stop_time = relationship(
        "StopTime",
        primaryjoin="""and_(foreign(Prediction.trip_id)==StopTime.trip_id,
                            foreign(Prediction.stop_id)==StopTime.stop_id,)""",
        viewonly=True,
        uselist=False,
    )

    DATETIME_MAPPER = {
        "arrival_time": "arrival_datetime",
        "departure_time": "departure_datetime",
    }

    REALTIME_NAME = "trip_updates"

    @reconstructor
    def _init_on_load_(self) -> None:
        """Converts arrival_time and departure_time to datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        self.predicted = self.__predict()
        self.stop_sequence = self.stop_sequence or 0

    def __predict(self) -> datetime | None:
        return (
            isoparse(self.arrival_time)
            if self.arrival_time
            else isoparse(self.departure_time)
            if self.departure_time
            else None
        )

    def status_as_html(self) -> str:
        """Returns status as html."""
        self.stop_sequence = self.stop_sequence or 0
        scheduled = self.stop_time.departure_datetime if self.stop_time else None
        delay = (
            int((self.predicted - scheduled).total_seconds() / 60)
            if (self.predicted and scheduled)
            else 0
        )
        if delay < -1400:
            delay += 1440
        if delay <= 2:
            return ""

        return f"""<span style="color:{self.__color(delay)};">{f"{str(delay)} minutes late"}</span>"""

    def as_html(self) -> str:
        """Returns prediction as html."""

        stop_name = (
            self.stop.parent_stop.stop_name
            if self.stop and self.stop.parent_stop
            else self.stop.stop_name
            if self.stop
            else ""
        )

        flag_stop = (
            "<div class = 'tooltip'>"
            f"<span class='flag_stop'>{stop_name}</span>"
            "<span class='tooltiptext'>Flag stop.</span></div>"
            if self.stop_time and self.stop_time.is_flag_stop()
            else ""
        )

        early_departure = (
            "<div class = 'tooltip'>"
            f"<span style='color:#2084d6;'>{stop_name}</span>"
            "<span class='tooltiptext'>Early departure stop.</span></div>"
            if self.stop_time and self.stop_time.is_early_departure()
            else ""
        )

        return (
            """<tr>"""
            f"""<td>{flag_stop or early_departure or stop_name}</td>"""
            f"""<td>{(self.stop.platform_name  if self.stop else "") or ""}</td>"""
            f"""<td>{self.predicted.strftime("%I:%M %p") if self.predicted else "Unknown"} {"—" if self.status_as_html() else ""} {self.status_as_html()}</td>"""
            """</tr>"""
        )

    def __color(self, delay: int) -> str:
        """Returns a color based on the delay.

        Args:
            delay (int): delay in minutes
        Returns:
            str: color
        """

        delay_dict = {
            "#ffffff": delay < 5,  # white
            "#ffff00": 5 <= delay < 10,
            "#ff8000": 10 <= delay < 15,
            "#ff0000": delay >= 15,
        }

        for color, condition in delay_dict.items():
            if condition:
                return color
