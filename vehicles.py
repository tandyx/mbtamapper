import sqlite3
import json
import logging
import requests as rq
import json_api_doc as jad
import pandas as pd

vehicle_type = 2

req = rq.get(f"https://api-v3.mbta.com/vehicles?include=trip%2Cstop%2Croute&filter%5Broute_type%5D={vehicle_type}", timeout=5)
if req.ok:
    vehicles = pd.DataFrame(jad.deserialization.deserialize(req.json()))
    print(vehicles)
    logging.info("Vehicles data retrieved successfully")
else:
    logging.error("Vehicles data retrieval failed")

