import sqlite3
import os
import time
import requests as rq
import json_api_doc as jad
import pandas as pd


def getvehicles(route_type=2, conn=sqlite3.connect("mbta_data.db")):
    """Retrieve vehicle data from MBTA API"""

    start_time = time.time()

    req = rq.get(
        f"https://api-v3.mbta.com/vehicles?filter[route_type]={route_type}&include=trip,stop,route&api_key={os.getenv('MBTA_API_KEY')}",
        timeout=5,
    )

    vehicles = pd.DataFrame()

    if req.ok and req.json()["data"]:
        mbta_response = pd.DataFrame(jad.deserialization.deserialize(req.json()))

        vehicles["vehicle_id"] = mbta_response["id"]
        vehicles["vehicle_label"] = mbta_response["label"]
        vehicles["stop_status"] = mbta_response["current_status"]
        vehicles["stop_sequence"] = mbta_response["current_stop_sequence"]
        vehicles["direction_id"] = mbta_response["direction_id"]
        # vehicles["label"] = mbta_response["label"]

        vehicles["latitude"] = mbta_response["latitude"]
        vehicles["longitude"] = mbta_response["longitude"]
        vehicles["bearing"] = mbta_response["bearing"]
        vehicles["speed"] = mbta_response["speed"]

        # vehicles["timestamp"] = iso_convert(mbta_response, ["updated_at"])
        vehicles["timestamp"] = pd.to_datetime(mbta_response["updated_at"])
        vehicles["trip_id"] = mbta_response["trip"].apply(lambda x: x["id"])
        vehicles["trip_short_name"] = mbta_response["trip"].apply(
            lambda x: x.get("name")
        )
        vehicles["bikes_allowed"] = mbta_response["trip"].apply(
            lambda x: x.get("bikes_allowed")
        )
        vehicles["headsign"] = mbta_response["trip"].apply(
            lambda x: x.get("headsign") if x else None
        )
        vehicles["stop"] = mbta_response["stop"].apply(
            lambda x: x.get("id") if x else None
        )

        vehicles["stop_name"] = mbta_response["stop"].apply(
            lambda x: x.get("name") if x else None
        )

        vehicles["route_id"] = mbta_response["route"].apply(
            lambda x: x.get("id") if x else None
        )
        vehicles["parent_station"] = mbta_response["stop"].apply(
            lambda x: x["parent_station"]["id"] if x and x["parent_station"] else None
        )
        vehicles["route_type"] = route_type

    vehicles.to_sql(f"vehicles_{route_type}", conn, if_exists="replace")

    print(
        f"Vehicles ({route_type}): fetched {len(vehicles)} vehicles in {(time.time() - start_time)} seconds"
    )
