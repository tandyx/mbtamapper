"""File to hold the LinkedDataset class and its associated methods."""

# pylint: disable=no-name-in-module
import logging
import typing as t

import pandas as pd
import requests as req
from google.protobuf.json_format import MessageToDict
from google.transit.gtfs_realtime_pb2 import FeedMessage
from sqlalchemy.orm import Mapped, mapped_column

from ..helper_functions.misc import df_unpack
from .base import Base

if t.TYPE_CHECKING:
    # pylint: disable=shadowed-import
    from google.protobuf.message import Message as FeedMessage


class LinkedDataset(Base):
    """LinkedDataset

    experimental, but useful to link and pull realtime info

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#linked_datasetstxt

    """

    __tablename__ = "linked_dataset"
    __filename__ = "linked_datasets.txt"

    url: Mapped[str] = mapped_column(primary_key=True)
    trip_updates: Mapped[int]
    vehicle_positions: Mapped[int]
    service_alerts: Mapped[int]
    authentication_type: Mapped[str]

    cache: dict[str, dict[str, t.Any]] = {}
    """Cache for linked datasets to avoid multiple requests."""

    @property
    def rename_dict(self) -> dict[str, str]:
        """returns the rename dict for this linked dataset

        Returns:
            dict[str, str]: _description_
        """

        if self.service_alerts:
            return {
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
        if self.vehicle_positions:
            return {
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
        if self.trip_updates:
            return {
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
                "timestamp": "timestamp",
            }
        return {}

    def cache_key(self, key: str = None, force: bool = False) -> dict[str, t.Any]:
        """Caches the linked dataset as a dictionary.
        Args:
            - key (str, optional): The key to use for the cache. If \
            not provided, the URL of the linked dataset is used.
            - force (bool, optional): Whether to force the cache to be updated.
        Returns:
            - dict[str, t.Any]: pointer to the cached linked dataset as a dict.
        """
        key = key or self.url
        if key not in self.__class__.cache or force:
            self.__class__.cache[key] = self.as_dict()
        return self.__class__.cache[key]

    def as_dataframe(self, ignore_errors: bool = True, **kwargs) -> pd.DataFrame:
        """Returns realtime data from the linked dataset\
            as a dataframe.
            
        args:
            ignore_errors (bool, optional): Whether to ignore errors when\
                loading the dataframe. Defaults to True.
            kwargs: Additional keyword arguments passed to the request.
        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """

        if not ignore_errors:
            return self._as_dataframe(**kwargs)
        try:
            return self._as_dataframe(**kwargs)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error retrieving data from %s: %s", self.url, str(e))
            return pd.DataFrame()

    def _as_dataframe(self, **kwargs) -> pd.DataFrame:
        """Returns realtime data from the linked dataset as a dataframe.
        args:
            **kwargs: Additional keyword arguments passed to the request.
        Returns:
            pd.DataFrame: Realtime data from the linked dataset."""

        if self.trip_updates:
            return self._process_trip_updates(**kwargs)
        if self.vehicle_positions:
            return self._process_vehicle_positions(**kwargs)
        if self.service_alerts:
            return self._process_service_alerts(**kwargs)
        return pd.DataFrame()

    def _load_dataframe(self, **kwargs) -> pd.DataFrame:
        """Returns realtime data from the linked dataset. any errors result in an empty dict

        args:
            **kwargs: Additional keyword arguments passed to the request.
        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
        feed_entity = FeedMessage()
        response = req.get(self.url, timeout=10, **kwargs)
        if not response.ok:
            logging.error("Error retrieving data from %s", self.url)
            return pd.DataFrame()
        logging.info("Retrieved data from %s", self.url)
        feed_entity.ParseFromString(response.content)
        if not hasattr(feed_entity, "entity"):
            logging.error("No data found in %s", self.url)
            return pd.DataFrame()
        msg_from_dict = MessageToDict(feed_entity, preserving_proto_field_name=True)
        dataframe = pd.json_normalize(msg_from_dict["entity"], sep="_")
        if not any(c in ["timestamp", "vehicle_timestamp"] for c in dataframe.columns):
            dataframe["timestamp"] = int(msg_from_dict["header"]["timestamp"])
        return dataframe

    def _post_process(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Args:
            dataframe: The dataframe to post process.
            rename_dict: The dictionary to rename the columns.\n
        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
        if not self.trip_updates:
            dataframe.drop_duplicates(["id"], inplace=True)
        dataframe.reset_index(drop=True, inplace=True)
        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in self.rename_dict],
            axis=1,
            inplace=True,
        )
        dataframe.rename(columns=self.rename_dict, inplace=True)
        return dataframe

    def _process_trip_updates(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """
        dataframe = df_unpack(self._load_dataframe(), "trip_update_stop_time_update")
        for col in [
            "trip_update_stop_time_update_departure",
            "trip_update_stop_time_update_arrival",
        ]:
            dataframe[col] = dataframe[col].apply(
                lambda x: int(x.get("time")) if isinstance(x, dict) else x
            )

        dataframe["trip_update_stop_time_update_stop_sequence"] = (
            dataframe["trip_update_stop_time_update_stop_sequence"]
            .fillna(0)
            .astype(int)
        )

        return self._post_process(dataframe)

    def _process_vehicle_positions(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
        """

        return self._post_process(self._load_dataframe())

    def _process_service_alerts(self) -> pd.DataFrame:
        """Returns realtime data from the linked dataset.

        Returns:
            pd.DataFrame: Realtime data from the linked dataset.
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
        return self._post_process(dataframe)
