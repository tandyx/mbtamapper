"""File to hold the LinkedDataset class and its associated methods."""

# pylint: disable=no-name-in-module
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import logging
import time

import pandas as pd
import requests as rq
from google.protobuf.json_format import MessageToDict
from google.transit.gtfs_realtime_pb2 import FeedMessage
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from helper_functions import *

from .gtfs_base import GTFSBase

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
    __filename__ = "linked_datasets.txt"

    url: str = mapped_column(String, primary_key=True)
    trip_updates: int = mapped_column(Integer)
    vehicle_positions: int = mapped_column(Integer)
    service_alerts: int = mapped_column(Integer)
    authentication_type: str = mapped_column(String)

    def as_dataframe(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset\
            as a dataframe.
            
        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """

        if self.trip_updates:
            return self._process_trip_updates()
        if self.vehicle_positions:
            return self._process_vehicle_positions()
        if self.service_alerts:
            return self._process_service_alerts()
        return pd.DataFrame()

    def _load_dataframe(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
        feed_entity = FeedMessage()
        response = rq.get(self.url, timeout=10)
        if not response.ok:
            logging.error("Error retrieving data from %s", self.url)
            return pd.DataFrame()
        logging.info("Retrieved data from %s", self.url)
        feed_entity.ParseFromString(response.content)
        if not hasattr(feed_entity, "entity"):
            logging.error("No data found in %s", self.url)
            return pd.DataFrame()
        return pd.json_normalize(
            MessageToDict(feed_entity, preserving_proto_field_name=True)["entity"],
            sep="_",
        )

    # from flatten_json import flatten

    def _post_process(self, dataframe: pd.DataFrame, rename_dict: dict) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Args:
            dataframe: The dataframe to post process.
            rename_dict: The dictionary to rename the columns.
        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """

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

    def _process_trip_updates(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
        dataframe = df_unpack(self._load_dataframe(), ["trip_update_stop_time_update"])
        for col in (
            "trip_update_stop_time_update_departure",
            "trip_update_stop_time_update_arrival",
        ):
            dataframe[col] = timestamp_col_to_iso(dataframe, col)

        dataframe["trip_update_stop_time_update_stop_sequence"] = (
            dataframe["trip_update_stop_time_update_stop_sequence"]
            .fillna(0)
            .astype(int)
        )
        return self._post_process(dataframe, PREDICTION_RENAME_DICT)

    def _process_vehicle_positions(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """

        dataframe = self._load_dataframe()
        dataframe = dataframe[
            (
                dataframe["vehicle_timestamp"].astype(int) > time.time() - 300
                if "vehicle_timestamp" in dataframe.columns
                else True
            )
        ]
        dataframe["vehicle_timestamp"] = timestamp_col_to_iso(
            dataframe, "vehicle_timestamp"
        )

        return self._post_process(dataframe, VEHICLE_RENAME_DICT)

    def _process_service_alerts(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
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
                lambda x: x.get("trip_id") if not pd.isna(x) else None
            )
            if "alert_informed_entity_trip" in dataframe.columns
            else None
        )
        dataframe["timestamp"] = get_current_time().isoformat()

        for col in ("alert_active_period_start", "alert_active_period_end"):
            dataframe[col] = timestamp_col_to_iso(dataframe, col)

        return self._post_process(dataframe, ALERT_RENAME_DICT)
