"""LinkedDatasets"""
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
import logging
import requests as rq
import pandas as pd
from google.transit.gtfs_realtime_pb2 import FeedMessage
from protobuf_to_dict import protobuf_to_dict
from sqlalchemy import Integer, Column, String
from sqlalchemy.orm import Session

from gtfs_loader.gtfs_base import GTFSBase
from gtfs_realtime import *

from helper_functions import df_unpack, timestamp_col_to_iso, get_current_time, to_sql

ALERT_RENAME_DICT = {
    "id": "alert_id",
    "alert_cause": "cause",
    "alert_effect": "effect",
    "alert_severity_level": "severity",
    "alert_informed_entity_stop_id": "stop_id",
    "alert_informed_entity_agency_id": "agency_id",
    "alert_informed_entity_route_id": "route_id",
    "alert_informed_entity_route_type": "route_type",
    "alert_informed_entity_direction_id": "direction_id",
    "alert_informed_entity_trip": "trip_id",
    "alert_active_period_end": "active_period_end",
    "alert_header_text_translation_text": "header",
    "alert_description_text_translation_text": "description",
    "alert_url_translation_text": "url",
    "alert_active_period_start": "active_period_start",
    "timestamp": "timestamp",
}
VEHICLE_RENAME_DICT = {
    "id": "vehicle_id",
    "vehicle_trip_trip_id": "trip_id",
    "vehicle_trip_route_id": "route_id",
    "vehicle_trip_direction_id": "direction_id",
    "vehicle_position_latitude": "latitude",
    "vehicle_position_longitude": "longitude",
    "vehicle_position_bearing": "bearing",
    "vehicle_current_stop_sequence": "current_stop_sequence",
    "vehicle_current_status": "current_status",
    "vehicle_timestamp": "timestamp",
    "vehicle_stop_id": "stop_id",
    "vehicle_vehicle_label": "label",
    "vehicle_occupancy_status": "occupancy_status",
    "vehicle_occupancy_percentage": "occupancy_percentage",
    "vehicle_position_speed": "speed",
}
PREDICTION_RENAME_DICT = {
    "id": "prediction_id",
    "trip_update_stop_time_update_arrival": "arrival_time",
    "trip_update_stop_time_update_departure": "departure_time",
    "trip_update_trip_direction_id": "direction_id",
    "stop_time_update_schedule_relationship": "schedule_relationship",
    "stop_time_update_stop_sequence": "stop_sequence",
    "trip_update_trip_route_id": "route_id",
    "trip_update_stop_time_update_stop_id": "stop_id",
    "trip_update_trip_trip_id": "trip_id",
    "trip_update_vehicle_id": "vehicle_id",
}
ALERT_UNPACK = [
    "alert_informed_entity",
    "alert_active_period",
    "alert_header_text_translation",
    "alert_description_text_translation",
    "alert_url_translation",
]
VEHICLE_UNPACK = []
TRIPUPDATES_UNPACK = ["trip_update_stop_time_update"]
ALERT_CONVERT = ["alert_active_period_start", "alert_active_period_end"]
VEHICLE_CONVERT = ["vehicle_timestamp"]
PREDICTION_CONVERT = [
    "trip_update_stop_time_update_departure",
    "trip_update_stop_time_update_arrival",
]


class LinkedDataset(GTFSBase):
    """LinkedDataset"""

    __tablename__ = "linked_datasets"

    url = Column(String, primary_key=True)
    trip_updates = Column(Integer)
    vehicle_positions = Column(Integer)
    service_alerts = Column(Integer)
    authentication_type = Column(String)

    DATASET_MAPPER = {
        "trip_updates": {
            "rename": PREDICTION_RENAME_DICT,
            "unpack": TRIPUPDATES_UNPACK,
            "convert": PREDICTION_CONVERT,
            "class": Prediction,
        },
        "vehicle_positions": {
            "rename": VEHICLE_RENAME_DICT,
            "unpack": VEHICLE_UNPACK,
            "convert": VEHICLE_CONVERT,
            "class": Vehicle,
        },
        "service_alerts": {
            "rename": ALERT_RENAME_DICT,
            "unpack": ALERT_UNPACK,
            "convert": ALERT_CONVERT,
            "class": Alert,
        },
    }

    def __repr__(self) -> str:
        return f"<LinkedDataset(url={self.url})>"

    def dump_realtime(self, session: Session) -> None:
        """Returns realtime data from the linked dataset."""

        feed = FeedMessage()
        response = rq.get(self.url, timeout=10)
        if not response.ok:
            logging.error(f"Error retrieving data from {self.url}")
            return
        else:
            logging.info(f"Retrieved data from {self.url}")

        feed.ParseFromString(response.content)

        for key, value in self.DATASET_MAPPER.items():
            if getattr(self, key):
                dataset_dict = value

        dataframe = df_unpack(
            pd.json_normalize(protobuf_to_dict(feed)["entity"], sep="_"),
            dataset_dict["unpack"],
        )

        if getattr(self, "service_alerts"):
            dataframe["alert_informed_entity_trip"] = dataframe[
                "alert_informed_entity_trip"
            ].apply(lambda x: x.get("trip_id") if x == x else None)

            dataframe["timestamp"] = get_current_time().isoformat()

        dataframe.reset_index(drop=True, inplace=True)

        for col in dataset_dict["convert"]:
            dataframe[col] = timestamp_col_to_iso(dataframe, col)

        dataframe.drop(
            columns=[
                col for col in dataframe.columns if col not in dataset_dict["rename"]
            ],
            inplace=True,
            axis=1,
        )
        dataframe.rename(columns=dataset_dict["rename"], inplace=True)
        dataframe["index"] = dataframe.index

        to_sql(session, dataframe, dataset_dict["class"], True)
