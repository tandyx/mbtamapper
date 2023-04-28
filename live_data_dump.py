import time
import sqlite3
import pandas as pd

import vehicles
import alerts
import poll_mbta_data.predictions as predictions
from shared_code.csv_ops import CSV_ops


def dump_data(delay=0, buses=False, conn=sqlite3.connect(f"mbta_data.db")):
    """Dump data to sqlite database from MBTA API"""

    timestamp = time.time()
    routes = pd.read_csv(CSV_ops("routes").get_latest())

    route_types = [0, 1, 2, 4]
    if buses:
        route_types.append(3)

    for route_type in route_types:
        loop_timestamp = time.time()
        active_routes = ",".join(
            routes.loc[routes["route_type"] == route_type]["route_id"].tolist()
        )

        vehicle_df = vehicles.getvehicles(route_type)

        alerts_df = alerts.getalerts(route_type)
        predictions_df = predictions.getpredictions(route_type, active_routes)

        header = True if route_type == 0 else False

        if not predictions_df.empty:
            predictions_df.to_csv(
                f"data/predictions_{int(timestamp)}.csv",
                mode="a",
                index=False,
                header=header,
            )

            predictions_df.to_sql(
                name=f"predictions_{route_type}", con=conn, if_exists="replace"
            )

        if not alerts_df.empty:
            alerts_df.to_csv(
                f"data/alerts_{int(timestamp)}.csv",
                mode="a",
                index=False,
                header=header,
            )

            alerts_df.to_sql(
                name=f"predictions_{route_type}", con=conn, if_exists="replace"
            )
        if not vehicle_df.empty:
            vehicle_df.to_csv(
                f"data/vehicles_{int(timestamp)}.csv",
                mode="a",
                index=False,
                header=header,
            )
            vehicle_df.to_sql(f"vehicles_{route_type}", con=conn, if_exists="replace")
        print(
            f"dumped route_type {route_type} live data in {time.time()-loop_timestamp} seconds"
        )
    print(f"data dumped in {time.time()-timestamp} seconds")
    for file_prefix in ["alerts", "predictions", "vehicles"]:
        CSV_ops(file_prefix).delete_old_data()

    time.sleep(delay)
