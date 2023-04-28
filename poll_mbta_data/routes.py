import sqlite3
import logging
import os
import time
from datetime import datetime
import pandas as pd
import json_api_doc as jad
import requests
import pytz
import numpy as np

# pylint: disable=unused-argument
# pylint: disable=unused-variable


def getroutes(route_type=2, conn=sqlite3.connect("mbta_data.db")):
    start_time = time.time()
    req = requests.get(
        f"https://api-v3.mbta.com/routes?filter%5Btype%5D={route_type}&api_key={os.getenv('MBTA_API_KEY')}",
        timeout=5,
    )
    routes = pd.DataFrame()
    if req.ok and req.json()["data"]:
        mbta_response = pd.DataFrame(req.json()["data"])
        if not mbta_response.empty:
            routes["route_id"] = mbta_response["id"]
            routes["route_name"] = mbta_response["attributes"].apply(
                lambda x: x["long_name"] if x else None
            )
            routes["description"] = mbta_response["attributes"].apply(
                lambda x: x["description"] if x else None
            )
            routes["route_type"] = route_type
            active_routes = ",".join(routes["route_id"].tolist())
    else:
        active_routes = ""

    routes.to_sql(f"routes_{route_type}", conn, if_exists="replace")
    print(
        f"Routes ({route_type}): fetched {len(routes)} routes in {(time.time() - start_time)} seconds"
    )
    return active_routes
