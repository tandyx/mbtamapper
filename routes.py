"""Keolis AVL-ACSES Real-Time Interface
Azure Function to poll MBTA API to get query active routes, trips and
match with route shape data. Creates two tables everyday at 2 am,
for the next service day beginning at 3 am, tripshapes and shapes.
2023-02-07
Keolis Digital Solutions - Service Delivery Team"""

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


def import_mbta_shapes(route_type=2):
    """Import MBTA shapes data from API"""

    trip_route_shape_fields = [
        "RowKey",
        "MBTAShape",
        "MBTAPolyLine",
        "MBTADirection",
        "MBTARouteType",
        "MBTARoute",
    ]

    routes_connection = requests.get(
        f"https://api-v3.mbta.com/routes?filter%5Btype%5D={route_type}&api_key={os.getenv('MBTA_API_KEY')}",
        timeout=5,
    )

    if routes_connection.ok:
        # creates a comma separated string of active routes
        active_routes = ",".join(
            [d["id"] for d in jad.deserialize(routes_connection.json()) if "id" in d]
        )

        try:
            route_trip_request = requests.get(
                str(
                    "https://api-v3.mbta.com/trips?"
                    + (
                        f"include=shape%2Croute&filter%5Broute%5D={active_routes}&api_key={os.getenv('MBTA_API_KEY')}"
                    )
                ),
                timeout=5,
            )
            route_trip = pd.DataFrame.from_dict(
                jad.deserialize(route_trip_request.json())
            )
            # issues with jad deserialization forced us to use this to query route type
            route_type_trip = pd.DataFrame.from_dict(
                route_trip_request.json()["included"],
            )

        except KeyError as error:
            logging.error(
                "poll_mbta_shapes couldn't get data from trips api: %s", error
            )
        # because shape, trip, route, etc. ids are listed only as "id"
        # they must be renamed when they're exploded.
        # route type trip only has route id and route type

        route_type_trip["MBTARouteType"] = route_type_trip.apply(
            lambda x: x["attributes"]["type"] if x["type"] == "route" else np.nan,
            axis=1,
        )

        route_trip["RowKey"] = route_trip["name"]
        route_trip["MBTADirection"] = route_trip["direction_id"]
        route_trip["MBTAShape"] = route_trip.apply(lambda x: x["shape"]["id"], axis=1)
        route_trip["MBTAPolyLine"] = route_trip.apply(
            lambda x: x["shape"]["polyline"], axis=1
        )
        route_trip["MBTARoute"] = route_trip.apply(lambda x: x["route"]["id"], axis=1)

        # appends route type onto main dataframe
        route_trip = pd.merge(
            route_trip, route_type_trip, how="left", left_on="MBTARoute", right_on="id"
        ).drop_duplicates(subset=["name"])

        route_trip = route_trip[route_trip["RowKey"] != ""].drop(
            columns=[col for col in route_trip if col not in trip_route_shape_fields]
        )

        # creates a copy of route_trip,
        # and drops duplicate mbtashape ids, which will be the RowKey.
        route_shapes = (
            route_trip.drop_duplicates(
                subset=["MBTAShape", "MBTARouteType", "MBTAPolyLine"]
            )
            .drop(columns=["MBTADirection"])
            .copy()
        ).reset_index(drop=True)

        return route_shapes

    else:
        logging.error(
            "import_mbta_shapes couldn't connect to mbta routes: %s",
            routes_connection.text,
        )


x = import_mbta_shapes()
