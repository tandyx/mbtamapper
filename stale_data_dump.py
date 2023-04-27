import sqlite3
import time
import logging
import pandas as pd

from shared_code.csv_ops import CSV_ops

import routes
import stops
import shapes


def dump_data(delay=6000, buses=False):
    while True:
        timestamp = time.time()
        route_types = [0, 1, 2, 4]
        if buses:
            route_types.append(3)

        for route_type in route_types:
            loop_timestamp = time.time()
            routes_df = routes.getroutes(route_type)
            active_routes = ",".join(routes_df["route_id"].unique().tolist())

            stops_df = stops.getstops(route_type)
            shapes_df = shapes.getshapes(route_type, active_routes)

            header = True if route_type == 0 else False

            if not stops_df.empty:
                stops_df.to_csv(
                    f"data/stops_{int(timestamp)}.csv",
                    mode="a",
                    index=False,
                    header=header,
                )
            if not shapes_df.empty:
                shapes_df.to_csv(
                    f"data/shapes_{int(timestamp)}.csv",
                    mode="a",
                    index=False,
                    header=header,
                )
            if not routes_df.empty:
                routes_df.to_csv(
                    f"data/routes_{int(timestamp)}.csv",
                    mode="a",
                    index=False,
                    header=header,
                )
            print(
                f"dumped route_type {route_type} stale data in {time.time()-loop_timestamp} seconds"
            )
        print(f"stale data dumped in {time.time()-timestamp} seconds")
        time.sleep(delay)
        for file_prefix in ["routes", "shapes", "stops"]:
            CSV_ops(file_prefix).delete_old_data()
