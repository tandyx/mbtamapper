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


def getshapes(route_type=2, active_routes="", conn=sqlite3.connect("mbta_data.db")):
    """Import MBTA shapes data from API"""

    start_time = time.time()

    trip_route_shape_fields = [
        "shape_id",
        "polyline",
        "route_type",
        "route_id",
        "route_color",
        "parent_route_type",
    ]

    req = requests.get(
        "https://api-v3.mbta.com/trips?"
        + (
            f"include=shape%2Croute&filter%5Broute%5D={active_routes}&api_key={os.getenv('MBTA_API_KEY')}"
        ),
        timeout=50,
    )

    route_trip = pd.DataFrame()

    if req.ok and req.json()["data"]:
        route_trip = pd.DataFrame.from_dict(jad.deserialize(req.json()))
        # issues with jad deserialization forced us to use this to query route type
        route_type_trip = pd.DataFrame.from_dict(
            req.json()["included"],
        )

        route_type_trip = route_type_trip.loc[
            route_type_trip["type"] == "route"
        ].reset_index(drop=True)

        route_type_trip["route_type"] = route_type_trip.apply(
            lambda x: x["attributes"]["type"], axis=1
        )
        route_type_trip["route_color"] = route_type_trip.apply(
            lambda x: x["attributes"]["color"], axis=1
        )
        route_trip["shape_id"] = route_trip.apply(
            lambda x: x["shape"]["id"] if x["shape"] else np.nan, axis=1
        )
        route_trip["polyline"] = route_trip.apply(
            lambda x: x["shape"]["polyline"] if x["shape"] else np.nan, axis=1
        )
        route_trip["route_id"] = route_trip.apply(
            lambda x: x["route"]["id"] if x["route"] else np.nan, axis=1
        )

        route_trip["parent_route_type"] = route_type

        # appends route type onto main dataframe
        route_trip = pd.merge(
            route_trip,
            route_type_trip,
            how="left",
            left_on="route_id",
            right_on="id",
        )

        route_trip = (
            route_trip.drop(
                columns=[
                    col
                    for col in route_trip.columns
                    if col not in trip_route_shape_fields
                ]
            )
            .reset_index(drop=True)
            .dropna()
            .drop_duplicates()
        )
        # stops["timestamp"] = pd.Timestamp.now(tz="America/New_York")

        route_trip.to_sql(f"shapes_{route_type}", conn, if_exists="replace")

        print(
            f"Shapes ({route_type}): fetched {len(route_trip)} shapes in {(time.time() - start_time)} seconds"
        )
