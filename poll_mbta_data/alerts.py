import time
import requests as rq
import pandas as pd
import json_api_doc as jad
import sqlite3


# pylint: disable=unused-argument
def getalerts(route_type=2, conn=sqlite3.connect("mbta_data.db")):
    """Import MBTA alerts data from API"""
    # polls CR T-alerts data from MBTA

    start_time = time.time()
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

    alerts.to_sql(f"alerts_{route_type}", conn, if_exists="replace")

    print(
        f"Routes ({route_type}): fetched {len(alerts)} alerts in {(time.time() - start_time)} seconds"
    )
