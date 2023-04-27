import logging
import requests as rq
import pandas as pd
import json_api_doc as jad


# pylint: disable=unused-argument
def getalerts(route_type=2):
    """Import MBTA alerts data from API"""
    # polls CR T-alerts data from MBTA
    req = rq.get(
        f"https://api-v3.mbta.com/alerts?filter[route_type]={route_type}&filter[datetime]=NOW&include=routes,trips",
        timeout=5,
    )
    alerts = pd.DataFrame()
    if req.ok and req.json()["data"]:
        mbta_response = pd.DataFrame(jad.deserialization.deserialize(req.json()))

        alerts["alert_id"] = mbta_response["id"]
        alerts["header"] = mbta_response["header"]
        alerts["effect"] = mbta_response["effect"]
        alerts["timestamp"] = mbta_response["updated_at"]
        alerts["link"] = mbta_response["url"]
        alerts["timeframe"] = mbta_response["timeframe"]
        alerts["short_header"] = mbta_response["short_header"]
        alerts["description"] = mbta_response["description"]

        alerts["cause"] = mbta_response["cause"]
        alerts["start_time"] = mbta_response["active_period"].apply(
            lambda x: x[0]["start"]
        )
        alerts["end_time"] = mbta_response["active_period"].apply(lambda x: x[0]["end"])

        alerts["route_id"] = mbta_response["informed_entity"].apply(
            lambda x: [item["route"] for item in x]
        )
        alerts["trip_id"] = mbta_response["informed_entity"].apply(
            lambda x: [item.get("trip") for item in x]
        )
        alerts["stop_id"] = mbta_response["informed_entity"].apply(
            lambda x: [item.get("stop") for item in x]
        )
        alerts["route_type"] = 2

        alerts = alerts.explode(["route_id", "trip_id", "stop_id"])

    logging.info("Received code %s from MBTA alerts", req.status_code)

    return alerts.reset_index(drop=True)
