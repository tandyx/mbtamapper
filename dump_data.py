import sqlite3
import time
import logging
import pandas as pd

import vehicles
import routes
import stops
import shapes
import alerts
import predictions


def dump_data(conn=sqlite3.connect("mbta.db")):
    """Dump data to sqlite database from MBTA API"""
    cursor = conn.cursor()
    cursor.execute("""PRAGMA writable_schema = 1;""")
    cursor.execute(
        """delete from sqlite_master where type in ('table', 'index', 'trigger');"""
    )
    cursor.execute("""PRAGMA writable_schema = 0;""")
    while True:
        for route_type in range(5):
            route_df = routes.getroutes(route_type)
            active_routes = ",".join(route_df["route_id"].unique().tolist())

            vehicle_df = vehicles.getvehicles(route_type)
            stops_df = stops.getstops(route_type)
            shapes_df = shapes.getshapes(route_type, active_routes)
            alerts_df = alerts.getalerts(route_type)
            predictions_df = predictions.getpredictions(route_type, active_routes)

            if not stops_df.empty:
                stops_df.to_sql(
                    "stops", conn, schema="online", index=False, if_exists="append"
                )
            if not predictions_df.empty:
                predictions_df.to_sql("predictions", conn, if_exists="append")
            if not shapes_df.empty:
                shapes_df.to_sql("shapes", conn, if_exists="append")
            if not alerts_df.empty:
                alerts_df.to_sql("alerts", conn, if_exists="append")
            if not vehicle_df.empty:
                vehicle_df.to_sql("vehicles", conn, if_exists="append")
            if not route_df.empty:
                route_df.to_sql("routes", conn, if_exists="append")

        logging.info("Data dump complete")
        time.sleep(60)


dump_data()
