"""Poll MBTA alerts data from API and store in SQLite database"""
import os
import time
import logging
import requests as rq
import pandas as pd
import numpy as np

from shared_code.df_unpack import df_unpack

RENAME_DICT = {
    "id": "alert_id",
    "type": "alert_type",
    "attributes_banner": "banner",
    "attributes_cause": "cause",
    "attributes_created_at": "created_at",
    "attributes_description": "description",
    "attributes_effect": "effect",
    "attributes_header": "header",
    "attributes_lifecycle": "lifecycle",
    "attributes_service_effect": "service_effect",
    "attributes_severity": "severity",
    "attributes_short_header": "short_header",
    "attributes_timeframe": "timeframe",
    "attributes_updated_at": "updated_at",
    "attributes_url": "url",
    "links_self": "links_self",
    "attributes_active_period_end": "active_period_end",
    "attributes_active_period_start": "active_period_start",
    # "attributes_informed_entity_activities": "informed_entity_activities",
    "attributes_informed_entity_direction_id": "direction_id",
    "attributes_informed_entity_route": "route_id",
    "attributes_informed_entity_route_type": "route_type",
    "attributes_informed_entity_trip": "trip_id",
    "attributes_informed_entity_stop": "stop_id",
}

UNPACK_LIST = ["attributes_active_period", "attributes_informed_entity"]


def get_alerts(route_type: str = "2") -> pd.DataFrame:
    """Downloads realtime alerts data from the mbta api.

    Args:
        route_type (str, optional): route type to download. Defaults to "2".
    Returns:
        pd.DataFrame: realtime alerts data"""
    start_time = time.time()

    url = (
        os.environ.get("MBTA_API_URL")
        + "/alerts?filter[route_type]="
        + route_type
        + "&filter[datetime]=NOW&include=routes,trips&api_key="
        + os.environ.get("MBTA_API_Key")
    )

    req = rq.get(url, timeout=500)

    if req.ok:
        dataframe = df_unpack(
            pd.json_normalize(req.json()["data"], sep="_"), UNPACK_LIST
        )
    else:
        logging.error("Error downloading realtime data from %s", url)
        dataframe = pd.DataFrame()

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in RENAME_DICT],
        axis=1,
        inplace=True,
    )

    dataframe.rename(columns=RENAME_DICT, inplace=True)

    for col in ["trip_id", "stop_id", "direction_id"]:
        if col not in dataframe.columns:
            dataframe[col] = np.nan

    logging.info(
        "Downloaded realtime alerts data from %s in %s seconds",
        url,
        time.time() - start_time,
    )

    return dataframe.reset_index(drop=True)
