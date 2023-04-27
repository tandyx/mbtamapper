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


def getroutes(route_type=2):
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
            routes["Description"] = mbta_response["attributes"].apply(
                lambda x: x["description"] if x else None
            )

    else:
        logging.error("Routes data retrieval failed")
    return routes
