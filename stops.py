import os
import requests as rq
import logging

import pandas as pd
import numpy as np
import geopandas as gpd
import json_api_doc as jad


def getstops(vehicle_type=2):
    req = rq.get(
        f"https://api-v3.mbta.com/stops?filter[route_type]={vehicle_type}&include=child_stops,connecting_stops,facilities,parent_station,route&api_key={os.getenv('MBTA_API_KEY')}",
        timeout=5,
    )

    if req.ok:
        mbta_response = pd.DataFrame(jad.deserialization.deserialize(req.json()))

        stops = pd.DataFrame()
        stops["stop_id"] = mbta_response["id"]
        stops["stop_name"] = mbta_response["name"]
        stops["latitude"] = mbta_response["latitude"]
        stops["longitude"] = mbta_response["longitude"]
        stops["platform_code"] = mbta_response["platform_code"]
        stops["municipality"] = mbta_response["municipality"]
        stops["wheelchair_accessible"] = mbta_response["wheelchair_boarding"]
        stops["parent_station"] = mbta_response["parent_station"].apply(
            lambda x: x["id"]
        )
        stops["adress"] = mbta_response["parent_station"].apply(lambda x: x["address"])
        stops["zone"] = mbta_response["zone"].apply(lambda x: x["id"])

        return gpd.GeoDataFrame(
            stops,
            geometry=gpd.points_from_xy(stops.longitude, stops.latitude, crs=4326),
        )
    else:
        logging.error("Vehicles data retrieval failed")
