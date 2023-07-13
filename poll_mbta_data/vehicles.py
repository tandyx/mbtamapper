"""Polls the MBTA API for realtime vehicle data and returns a dataframe with the data."""
import os
import requests as rq
import logging
import pandas as pd

RENAME_DICT = {
    "id": "vehicle_id",
    "type": "vehicle_type",
    "attributes_bearing": "bearing",
    "attributes_current_status": "current_status",
    "attributes_current_stop_sequence": "current_stop_sequence",
    "attributes_direction_id": "direction_id",
    "attributes_label": "label",
    "attributes_latitude": "latitude",
    "attributes_longitude": "longitude",
    "attributes_occupancy_status": "occupancy_status",
    "attributes_speed": "speed",
    "attributes_updated_at": "updated_at",
    "links_self": "links_self",
    "relationships_route_data_id": "route_id",
    "relationships_stop_data_id": "stop_id",
    "relationships_trip_data_id": "trip_id",
}


def get_vehicles(route_type: str = "2") -> pd.DataFrame:
    """Downloads realtime vehicle data from the mbta api."""

    url = (
        os.environ.get("MBTA_API_URL")
        + "/vehicles?filter[route_type]="
        + route_type
        + "&include=trip,stop,route&api_key="
        + os.environ.get("MBTA_API_Key")
    )

    req = rq.get(url, timeout=500)

    if req.ok:
        dataframe = pd.json_normalize(req.json()["data"], sep="_")
    else:
        logging.error("Failed to query vehicles: %s", req.text)
        dataframe = pd.DataFrame()

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in RENAME_DICT],
        axis=1,
        inplace=True,
    )

    dataframe.rename(columns=RENAME_DICT, inplace=True)

    return dataframe.reset_index()
