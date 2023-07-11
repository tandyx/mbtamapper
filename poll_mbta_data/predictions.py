"""Downloads realtime predictions data from the mbta api."""
import time
import logging
import os
import requests as rq
import pandas as pd

RENAME_DICT = {
    "id": "prediction_id",
    "type": "prediction_type",
    "attributes_arrival_time": "arrival_time",
    "attributes_departure_time": "departure_time",
    "attributes_direction_id": "direction_id",
    "attributes_schedule_relationship": "schedule_relationship",
    "attributes_status": "status",
    "attributes_stop_sequence": "stop_sequence",
    "relationships_route_data_id": "route_id",
    "relationships_schedule_data_id": "schedule_id",
    "relationships_stop_data_id": "stop_id",
    "relationships_trip_data_id": "trip_id",
    "relationships_vehicle_data_id": "vehicle_id",
}


def get_predictions(active_routes: str = "CR-Providence") -> pd.DataFrame:
    """Downloads realtime predictions data from the mbta api.

    Args:
        active_routes (str, optional): comma separated list of active routes. Defaults to "".
    Returns:
        pd.DataFrame: realtime predictions data
    """
    start_time = time.time()
    url = (
        os.environ.get("MBTA_API_URL")
        + "/predictions?filter[route]="
        + active_routes
        + "&include=stop,trip,route,vehicle,schedule&api_key="
        + os.environ.get("MBTA_API_Key")
    )

    req = rq.get(url, timeout=500)

    if req.ok:
        dataframe = pd.json_normalize(req.json()["data"], sep="_")
    else:
        logging.error("Error downloading realtime data from %s", url)
        dataframe = pd.DataFrame()

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in RENAME_DICT],
        axis=1,
        inplace=True,
    )

    dataframe.rename(columns=RENAME_DICT, inplace=True)

    logging.info(
        "Downloaded realtime predictions data from %s in %s seconds",
        url,
        time.time() - start_time,
    )

    return dataframe


if __name__ == "__main__":
    get_predictions()
