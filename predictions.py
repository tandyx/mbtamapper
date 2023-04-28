from datetime import datetime
import sqlite3
import time
import logging
import os
import requests as rq
import pytz
import pandas as pd
import json_api_doc as jad
from shared_code import calc_delay, iso_convert


# pylint: disable=unused-argument
def getpredictions(
    route_type=2, active_routes="", conn=sqlite3.connect("mbta_data.db")
):
    """Import MBTA predictions data from API"""

    start_time = time.time()

    req = rq.get(
        "https://api-v3.mbta.com/predictions?filter[route]="
        + active_routes
        + "&include=stop,trip,route,vehicle,schedule&api_key="
        + os.getenv("MBTA_API_Key"),
        timeout=500,
    )
    logging.info("Received code %s from MBTA predictions", req.status_code)

    predictions = pd.DataFrame()

    if req.ok and req.json()["data"]:
        mbta_response = pd.DataFrame(jad.deserialize(req.json()))

        predictions["vehicle_id"] = mbta_response["vehicle"].apply(
            lambda x: x["id"] if x else None
        )
        predictions["vehicle_label"] = mbta_response["vehicle"].apply(
            lambda x: x["label"] if x else None
        )
        predictions["route_id"] = mbta_response["route"].apply(
            lambda x: x["id"] if x else None
        )
        predictions["stop_id"] = mbta_response["stop"].apply(
            lambda x: x["id"] if x else None
        )
        predictions["stop_name"] = mbta_response["stop"].apply(
            lambda x: x["name"] if x else None
        )
        predictions["description"] = mbta_response["stop"].apply(
            lambda x: x["description"] if x else None
        )
        predictions["parent_station"] = mbta_response["stop"].apply(
            lambda x: x["parent_station"]["id"] if x and x["parent_station"] else None
        )
        predictions["platform_code"] = mbta_response["stop"].apply(
            lambda x: x["platform_code"] if x else None
        )
        predictions["platform_name"] = mbta_response["stop"].apply(
            lambda x: x["platform_name"] if x else None
        )
        predictions["trip_id"] = mbta_response["trip"].apply(
            lambda x: x["id"] if x else None
        )
        predictions["headsign"] = mbta_response["trip"].apply(
            lambda x: x["headsign"] if x else None
        )
        predictions["scheduled_arrival_time"] = mbta_response["schedule"].apply(
            lambda x: x["arrival_time"] if x else None
        )
        predictions["scheduled_departure_time"] = mbta_response["schedule"].apply(
            lambda x: x["departure_time"] if x else None
        )

        # iso_convert.iso_convert(
        #     predictions,
        #     [
        #         "scheduled_arrival_time",
        #         "scheduled_departure_time",
        #         "predicted_arrival_time",
        #         "predicted_departure_time",
        #     ],
        # )

        predictions["arrival_delay"] = calc_delay.calc_delay(
            predictions, "scheduled_arrival_time", "predicted_arrival_time"
        )
        predictions["departure_delay"] = calc_delay.calc_delay(
            predictions, "scheduled_departure_time", "predicted_departure_time"
        )

        predictions["status"] = mbta_response["status"]
        predictions["direction_id"] = mbta_response["direction_id"]
        predictions["predicted_arrival_time"] = mbta_response["arrival_time"]
        predictions["predicted_departure_time"] = mbta_response["departure_time"]
        predictions["stop_sequence"] = mbta_response["stop_sequence"]
        predictions["route_type"] = route_type
        predictions["timestamp"] = datetime.now(pytz.timezone("America/New_York"))

    predictions.to_sql(f"predictions_{route_type}", conn, if_exists="replace")
    return predictions
