"""File to hold the LinkedDataset class and its associated methods."""
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
import time
import logging
import requests as rq
import pandas as pd
from google.transit.gtfs_realtime_pb2 import FeedMessage
from protobuf_to_dict import protobuf_to_dict
from sqlalchemy import Integer, Column, String

from ..gtfs_base import GTFSBase
from ..realtime import *

from helper_functions import df_unpack, timestamp_col_to_iso, get_current_time

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
    "trip_update_stop_time_update_stop_sequence": "stop_sequence",
    "trip_update_trip_route_id": "route_id",
    "trip_update_stop_time_update_stop_id": "stop_id",
    "trip_update_trip_trip_id": "trip_id",
    "trip_update_vehicle_id": "vehicle_id",
}


class LinkedDataset(GTFSBase):
    """LinkedDataset"""

    __tablename__ = "linked_datasets"

    url = Column(String, primary_key=True)
    trip_updates = Column(Integer)
    vehicle_positions = Column(Integer)
    service_alerts = Column(Integer)
    authentication_type = Column(String)

    DATASET_MAPPER = {
        Prediction: "trip_updates",
        Vehicle: "vehicle_positions",
        Alert: "service_alerts",
    }

    def __repr__(self) -> str:
        return f"<LinkedDataset(url={self.url})>"

    def is_dataset(self, _orm: GTFSBase) -> bool:
        """Returns True if the object is a dataset."""
        return bool(getattr(self, LinkedDataset.DATASET_MAPPER.get(_orm), 0))

    def _load_dataframe(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset."""
        feed = FeedMessage()
        response = rq.get(self.url, timeout=10)
        if not response.ok:
            logging.error("Error retrieving data from %s", self.url)
            return pd.DataFrame()
        logging.info("Retrieved data from %s", self.url)
        feed.ParseFromString(response.content)
        return pd.json_normalize(protobuf_to_dict(feed)["entity"], sep="_")

    def _post_process(self, dataframe: pd.DataFrame, rename_dict: dict) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Args:
            dataframe: The dataframe to post process.
            rename_dict: The dictionary to rename the columns."""

        dataframe = (
            dataframe.reset_index(drop=True)
            .drop(
                columns=[col for col in dataframe.columns if col not in rename_dict],
                axis=1,
            )
            .rename(columns=rename_dict)
        )
        dataframe["index"] = dataframe.index

        return dataframe

    def process_trip_updates(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset."""
        dataframe = df_unpack(self._load_dataframe(), ["trip_update_stop_time_update"])
        dataframe["alert_informed_entity_trip"] = (
            dataframe["alert_informed_entity_trip"].apply(
                lambda x: x.get("trip_id") if x == x else None
            )
            if "alert_informed_entity_trip" in dataframe.columns
            else None
        )

        for col in [
            "trip_update_stop_time_update_departure",
            "trip_update_stop_time_update_arrival",
        ]:
            dataframe[col] = timestamp_col_to_iso(dataframe, col)

        dataframe["trip_update_stop_time_update_stop_sequence"] = (
            dataframe["trip_update_stop_time_update_stop_sequence"]
            .fillna(0)
            .astype(int)
        )

        return self._post_process(dataframe, PREDICTION_RENAME_DICT)

    def process_vehicle_positions(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset."""

        dataframe = self._load_dataframe()
        dataframe["vehicle_position_speed"] = (
            dataframe["vehicle_position_speed"] * 2.23694
            if "vehicle_position_speed" in dataframe.columns
            else None
        )
        dataframe = dataframe[dataframe["vehicle_timestamp"] > time.time() - 300]
        dataframe["vehicle_timestamp"] = timestamp_col_to_iso(
            dataframe, "vehicle_timestamp"
        )
        return self._post_process(dataframe, VEHICLE_RENAME_DICT)

    def process_service_alerts(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset."""
        dataframe = df_unpack(
            self._load_dataframe(),
            [
                "alert_informed_entity",
                "alert_active_period",
                "alert_header_text_translation",
                "alert_description_text_translation",
                "alert_url_translation",
            ],
        )
        dataframe["alert_informed_entity_trip"] = (
            dataframe["alert_informed_entity_trip"].apply(
                lambda x: x.get("trip_id") if x == x else None
            )
            if "alert_informed_entity_trip" in dataframe.columns
            else None
        )
        dataframe["timestamp"] = get_current_time().isoformat()

        for col in ["alert_active_period_start", "alert_active_period_end"]:
            dataframe[col] = timestamp_col_to_iso(dataframe, col)

        return self._post_process(dataframe, ALERT_RENAME_DICT)
