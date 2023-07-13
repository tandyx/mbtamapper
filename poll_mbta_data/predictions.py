"""Downloads realtime predictions data from the mbta api."""
import logging
import os
import requests as rq
import pandas as pd
import json_api_doc as jad

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


def get_predictions(active_routes: str = "CR-Providence,CR-Fitchburg") -> pd.DataFrame:
    """Downloads realtime predictions data from the mbta api.

    Args:
        active_routes (str, optional): comma separated list of active routes. Defaults to "".
    Returns:
        pd.DataFrame: realtime predictions data
    """
    url = (
        os.environ.get("MBTA_API_URL")
        + "/predictions?filter[route]="
        + active_routes
        + "&include=stop,trip,route,vehicle,schedule&api_key="
        + os.environ.get("MBTA_API_Key")
    )

    req = rq.get(url, timeout=500)

    if req.ok:
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

    return dataframe.reset_index(drop=True)
