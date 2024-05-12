"""File to hold the LinkedDataset class and its associated methods."""

# pylint: disable=no-name-in-module
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import logging
import time
from typing import TYPE_CHECKING

import pandas as pd
import requests as rq
from google.protobuf.json_format import MessageToDict
from google.transit.gtfs_realtime_pb2 import FeedMessage
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    import google.protobuf.message as pbm

    FeedMessage = pbm.Message

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


class LinkedDataset(Base):
    """LinkedDataset"""

    __tablename__ = "linked_datasets"
    __filename__ = "linked_datasets.txt"

    url: Mapped[str] = mapped_column(primary_key=True)
    trip_updates: Mapped[int]
    vehicle_positions: Mapped[int]
    service_alerts: Mapped[int]
    authentication_type: Mapped[str]

    def as_dataframe(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset\
            as a dataframe.
            
        Returns:
            - `pd.DataFrame`: Realtime data from the linked dataset.
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
            - `pd.DataFrame`: Realtime data from the linked dataset.
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
            - `dataframe`: The dataframe to post process.
            - `rename_dict`: The dictionary to rename the columns.\n
        Returns:
            - `pd.DataFrame`: Realtime data from the linked dataset.
        """
        if not self.trip_updates:
            dataframe.drop_duplicates("id", inplace=True)
        dataframe.reset_index(drop=True, inplace=True)
        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in rename_dict],
            axis=1,
            inplace=True,
        )
        dataframe.rename(columns=rename_dict, inplace=True)
        if self.trip_updates:
            dataframe["index"] = dataframe.index
        return dataframe

    def _process_trip_updates(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            - `pd.DataFrame`: Realtime data from the linked dataset.
        """
        dataframe = df_unpack(self._load_dataframe(), "trip_update_stop_time_update")
        for col in [
            "trip_update_stop_time_update_departure",
            "trip_update_stop_time_update_arrival",
        ]:
            dataframe[col] = dataframe[col].apply(
                lambda x: (int(x.get("time")) if isinstance(x, dict) else x)
            )

        dataframe["trip_update_stop_time_update_stop_sequence"] = (
            dataframe["trip_update_stop_time_update_stop_sequence"]
            .fillna(0)
            .astype(int)
        )

        return self._post_process(dataframe, PREDICTION_RENAME_DICT)

    def _process_vehicle_positions(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            - `pd.DataFrame`: Realtime data from the linked dataset.
        """

        dataframe = self._load_dataframe()
        dataframe = dataframe[
            (
                dataframe["vehicle_timestamp"].astype(int) > time.time() - 300
                if "vehicle_timestamp" in dataframe.columns
                else True
            )
        ]
        return self._post_process(dataframe, VEHICLE_RENAME_DICT)

    def _process_service_alerts(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            - `pd.DataFrame`: Realtime data from the linked dataset.
        """
        dataframe = df_unpack(
            self._load_dataframe(),
            "alert_informed_entity",
            "alert_active_period",
            "alert_header_text_translation",
            "alert_description_text_translation",
            "alert_url_translation",
        )
        dataframe["alert_informed_entity_trip"] = (
            dataframe["alert_informed_entity_trip"].apply(
                lambda x: x.get("trip_id") if not pd.isna(x) else None
            )
            if "alert_informed_entity_trip" in dataframe.columns
            else None
        )
        dataframe["timestamp"] = time.time()
        return self._post_process(dataframe, ALERT_RENAME_DICT)

    def as_feature(self, *include: str) -> None:
        """raises `NotImplementedError`"""
        raise NotImplementedError(f"Not implemented for {self.__class__.__name__}")


def df_unpack(
    dataframe: pd.DataFrame, *columns: str, prefix: bool = True
) -> pd.DataFrame:
    """Unpacks a column of a dataframe that contains a list of dictionaries. \
        Returns a dataframe with the unpacked column and the original dataframe\
        with the packed column removed.

    Args:
        - `dataframe (pd.DataFrame)`: dataframe to unpack
        - `*columns (str)`: columns to unpack.
        - `prefix (bool, optional)`: whether to add prefix to unpacked columns. \
            Defaults to True. \n
    Returns:
        - `pd.DataFrame`: dataframe with unpacked columns
    """

    for col in columns:
        if col not in dataframe.columns:
            continue
        exploded = dataframe.explode(col)
        series = exploded[col].apply(pd.Series)
        if prefix:
            series = series.add_prefix(col + "_")
        dataframe = pd.concat([exploded.drop([col], axis=1), series], axis=1)
    return dataframe
