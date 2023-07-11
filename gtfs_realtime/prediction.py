"""predictions"""
from datetime import datetime
from dateutil.parser import isoparse
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from gtfs_loader.gtfs_base import GTFSBase


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"

    prediction_id = Column(String, primary_key=True)
    prediction_type = Column(String)
    arrival_time = Column(String)
    departure_time = Column(String)
    scheduled_arrival_time = Column(String)
    scheduled_departure_time = Column(String)
    direction_id = Column(String)
    schedule_relationship = Column(String)
    status = Column(String)
    stop_sequence = Column(Integer)
    route_id = Column(String)
    stop_id = Column(String)
    trip_id = Column(String)
    vehicle_id = Column(String)

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
        "scheduled_arrival_time": "scheduled_arrival_datetime",
        "scheduled_departure_time": "scheduled_departure_datetime",
    }

    @reconstructor
    def init_on_load(self):
        """Converts arrival_time and departure_time to datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        for key, value in self.DATETIME_MAPPER.items():
            if getattr(self, key, None):
                setattr(self, value, isoparse(getattr(self, key)))

        self.predicted = checker(self, "departure_datetime", "arrival_datetime")
        self.scheduled = checker(
            self, "scheduled_departure_datetime", "scheduled_arrival_datetime"
        )

        self.delay = (
            int((self.predicted - self.scheduled).total_seconds() / 60)
            if (self.predicted and self.scheduled)
            else 0
        )

    def __repr__(self):
        return f"<Prediction(id={self.prediction_id})>"

    def as_dict(self):
        """Returns prediction as dict."""
        prediction = {
            "stop": self.stop.parent_stop.stop_name,
            "trip": self.trip.as_label(),
            "status": self.status,
            "route": self.route.route_short_name or self.route.route_long_name,
            "delay": self.delay,
        }

        for key, value in {
            "predicted": self.predicted,
            "scheduled": self.scheduled,
        }.items():
            if value:
                prediction[key] = value.strftime("%I:%M%p")

        return prediction


def checker(_obj, attr1: str, attr2: str):
    """Checks if attribute is set."""
    return getattr(_obj, attr1, None) or getattr(_obj, attr2, None)
