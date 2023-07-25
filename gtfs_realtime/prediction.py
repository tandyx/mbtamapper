"""predictions"""
# pylint: disable=line-too-long
from dateutil.parser import isoparse

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase

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
                            foreign(Prediction.stop_sequence)==StopTime.stop_sequence,
                            foreign(Prediction.stop_id)==StopTime.stop_id,)""",
        viewonly=True,
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
        self.scheduled = self.stop_time.departure_datetime if self.stop_time else None
        self.delay = (
            int((self.predicted - self.scheduled).total_seconds() / 60)
            if (self.predicted and self.scheduled)
            else 0
        )

        self.stop_sequence = self.stop_sequence or 0

    def __repr__(self):
        return f"<Prediction(id={self.prediction_id})>"

    def status_as_html(self) -> str:
        """Returns status as html."""

        if not self.predicted or not self.scheduled:
            return ""

        return f"""<a style="color:{return_delay_colors(self.delay)};">{f"({str(self.delay)} minutes late)" if self.delay > 2 else ""}</a>"""

    def as_html(self) -> str:
        """Returns prediction as html."""
        return (
            """<tr>"""
            f"""<td>{self.stop.parent_stop.stop_name if self.stop and self.stop.parent_stop else self.stop.stop_name}</td>"""
            f"""<td>{self.stop.platform_name}</td>"""
            f"""<td>{self.predicted.strftime("%I:%M %p") if self.predicted else "Unknown"} {self.status_as_html()}</td>"""
            """</tr>"""
        )


def checker(_obj, attr1: str, attr2: str):
    """Checks if attribute is set."""
    return getattr(_obj, attr1, None) or getattr(_obj, attr2, None)
