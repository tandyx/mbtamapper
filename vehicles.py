import sqlite3
import json
import logging
import requests as rq
import json_api_doc as jad
import pandas as pd
import geopandas as gpd

def getvehicles(vehicle_type=2):
    """Retrieve vehicle data from MBTA API"""
    
    req = rq.get(f"https://api-v3.mbta.com/vehicles?include=trip%2Cstop%2Croute&filter%5Broute_type%5D={vehicle_type}", timeout=5)

    if req.ok:
        mbta_response = pd.DataFrame(jad.deserialization.deserialize(req.json()))
        
        vehicles = pd.DataFrame()
        vehicles["vehicle_id"] = mbta_response["id"]
        vehicles["stop_status"] = mbta_response["current_status"]
        vehicles["stop_sequence"] = mbta_response["current_stop_sequence"]
        vehicles["direction_id"] = mbta_response["direction_id"]
        # vehicles["label"] = mbta_response["label"]
        vehicles["latitude"] = mbta_response["latitude"]
        vehicles["longitude"] = mbta_response["longitude"]
        vehicles["bearing"] = mbta_response["bearing"]
        vehicles["speed"] = mbta_response["speed"]
        vehicles["timestamp"] = mbta_response["timestamp"]
        
        logging.info("Vehicles data retrieved successfully")
        
        return gpd.GeoDataFrame(
        vehicles, geometry=gpd.points_from_xy(vehicles.longitude, vehicles.latitude, crs=4326)
        )

    else:
        logging.error("Vehicles data retrieval failed")

