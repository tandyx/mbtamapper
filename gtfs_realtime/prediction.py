"""predictions"""
import os
import logging
import requests
import pandas as pd
from dateutil.parser import isoparse
import json_api_doc as jad

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy.engine import Engine
from gtfs_loader.gtfs_base import GTFSBase
from shared_code.to_sql import to_sql


RENAME_DICT = {
    "id": "prediction_id",
    "type": "prediction_type",
    "arrival_time": "arrival_time",
    "departure_time": "departure_time",
    "direction_id": "direction_id",
    "schedule_relationship": "schedule_relationship",
    "status": "status",
    "stop_sequence": "stop_sequence",
    "schedule_arrival_time": "scheduled_arrival_time",
    "schedule_departure_time": "scheduled_departure_time",
    "route_id": "route_id",
    "stop_id": "stop_id",
    "trip_id": "trip_id",
    "vehicle_id": "vehicle_id",
}


class Prediction(GTFSBase):
    """Prediction"""

    __tablename__ = "predictions"

    prediction_id = Column(String)
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

    def status_as_string(self) -> str:
        """Returns status as string."""
        return f"({str(self.delay)} minutes late)" if self.delay > 2 else "(on time)"

    def get_realtime(
        self,
        engine: Engine,
        routes: str,
        base_url: str = None,
        api_key: str = None,
    ) -> None:
        """Downloads realtime predictions data from the mbta api.

        Args:
            engine (Engine): database engine
            routes (str): comma separated string of routes
            base_url (str, optional): base url for mbta api. Defaults to env var.
            api_key (str, optional): api key for mbta api. Defaults to env var.
        """
        url = (
            (base_url or os.environ.get("MBTA_API_URL"))
            + "/predictions?filter[route]="
            + routes
            + "&include=stop,trip,route,vehicle,schedule&api_key="
            + (api_key or os.environ.get("MBTA_API_Key"))
        )

        req = requests.get(url, timeout=500)

        if req.ok and req.json().get("data"):
            dataframe = pd.json_normalize(jad.deserialize(req.json()), sep="_")
        else:
            logging.error("Failed to query predictions: %s", req.text)
            dataframe = pd.DataFrame()

        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in RENAME_DICT],
            axis=1,
            inplace=True,
        )
        dataframe.rename(columns=RENAME_DICT, inplace=True)
        dataframe.reset_index()
        dataframe["index"] = dataframe.index
        self.metadata.drop_all(engine, [self.__table__])
        self.metadata.create_all(engine, [self.__table__])
        to_sql(engine, dataframe, self.__class__)


def checker(_obj, attr1: str, attr2: str):
    """Checks if attribute is set."""
    return getattr(_obj, attr1, None) or getattr(_obj, attr2, None)
