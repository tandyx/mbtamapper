"""
Keolis AVL-ACSES Real-Time Interface
Azure Function to poll MBTA data at /alerts and create live alerts table
2023-01-20
Keolis Digital Solutions - Service Delivery Team
"""
from datetime import datetime
import logging
import os
import requests as rq
import pytz
import pandas as pd
import json_api_doc as jad


# pylint: disable=unused-argument
def getalerts(route_type=2):
    """Import MBTA alerts data from API"""
    # polls CR T-alerts data from MBTA
    req = rq.get(
        "https://api-v3.mbta.com/alerts?filter[route_type]=2&filter[datetime]=NOW&include=routes,trips",
        timeout=5,
    )
    alerts = pd.DataFrame()
    if req.ok:
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

        alerts = alerts.explode(["route_id", "trip_id", "stop_id"])

        # [{'activities': [...], 'direction_id': 1, 'route': 'CR-Kingston', 'route_type': 2, 'trip': 'CR-554461-062'}]

    return alerts


getalerts(2)
