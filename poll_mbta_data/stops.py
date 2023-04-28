import os
import sqlite3
import requests as rq
import time

import pandas as pd
import numpy as np
import geopandas as gpd
import json_api_doc as jad


def getstops(route_type=2, conn=sqlite3.connect("mbta_data.db")):
    start_time = time.time()
    req = rq.get(
        f"https://api-v3.mbta.com/stops?filter[route_type]={route_type}&include=child_stops,connecting_stops,facilities,parent_station,route&api_key={os.getenv('MBTA_API_KEY')}",
        timeout=500,
    )
    stops = pd.DataFrame()

    if req.ok and req.json()["data"]:
        mbta_response = pd.DataFrame(jad.deserialization.deserialize(req.json()))

        stops["stop_id"] = mbta_response["id"]
        stops["stop_name"] = mbta_response["name"]
        stops["latitude"] = mbta_response["latitude"]
        stops["longitude"] = mbta_response["longitude"]
        stops["platform_code"] = mbta_response["platform_code"]
        stops["platform_name"] = mbta_response["platform_name"]
        stops["municipality"] = mbta_response["municipality"]
        stops["wheelchair_accessible"] = mbta_response["wheelchair_boarding"]
        stops["parent_station"] = mbta_response["parent_station"].apply(
            lambda x: x["id"] if x else None
        )

        stops["adress"] = mbta_response["parent_station"].apply(
            lambda x: x["address"] if x else None
        )
        stops["description"] = mbta_response["description"]
        stops["zone"] = mbta_response["zone"].apply(lambda x: x["id"] if x else None)
        stops["route_type"] = route_type

        stops["parent_station"] = stops["parent_station"].fillna(stops["stop_id"])
        stops["timestamp"] = pd.Timestamp.now(tz="America/New_York")
    stops.to_sql(f"stops_{route_type}", conn, if_exists="replace")
    print(
        f"Stops ({route_type}): fetched {len(stops)} stops in {(time.time() - start_time)} seconds"
    )
