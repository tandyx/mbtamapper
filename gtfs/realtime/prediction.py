"""File to hold the Prediction class and its associated methods."""
# pylint: disable=line-too-long
from dateutil.parser import isoparse

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from ..base import GTFSBase

from helper_functions import return_delay_colors


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

    @reconstructor
    def init_on_load(self):
        """Converts arrival_time and departure_time to datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        for key, value in self.DATETIME_MAPPER.items():
            if getattr(self, key, None):
                setattr(self, value, isoparse(getattr(self, key)))

        self.predicted = checker(self, "departure_datetime", "arrival_datetime")
        self.stop_sequence = self.stop_sequence or 0

    def __repr__(self):
        return f"<Prediction(id={self.prediction_id})>"

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

        return f"""<span style="color:{return_delay_colors(delay)};">{f"{str(delay)} minutes late"}</span>"""

    def as_html(self) -> str:
        """Returns prediction as html."""

        stop_name = (
            self.stop.parent_stop.stop_name
            if self.stop and self.stop.parent_stop
            else self.stop.stop_name
        )

        flag_stop = (
            "<div class = 'tooltip'>"
            f"<span style='color:#c73ca8;'>{stop_name}</span>"
            "<span class='tooltiptext'>Flag stop.</span></div>"
            if self.trip
            and self.stop_time
            and self.trip.route.route_type == "2"
            and (
                self.stop_time.pickup_type == "3" or self.stop_time.drop_off_type == "3"
            )
            else ""
        )

        early_departure = (
            "<div class = 'tooltip'>"
            f"<span style='color:#2084d6;'>{stop_name}</span>"
            "<span class='tooltiptext'>Early departure stop.</span></div>"
            if self.trip
            and self.stop_time
            and self.trip.route.route_type == "2"
            and self.stop_time.timepoint == "0"
            and not self.stop_time.is_destination()
            else ""
        )

        return (
            """<tr>"""
            f"""<td>{flag_stop or early_departure or stop_name}</td>"""
            f"""<td>{self.stop.platform_name or ""}</td>"""
            f"""<td>{self.predicted.strftime("%I:%M %p") if self.predicted else "Unknown"} {"—" if self.status_as_html() else ""} {self.status_as_html()}</td>"""
            """</tr>"""
        )


def checker(_obj, attr1: str, attr2: str):
    """Checks if attribute is set."""
    return getattr(_obj, attr1, None) or getattr(_obj, attr2, None)
