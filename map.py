import time
import logging
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import numpy as np
import pandas as pd
import geocoder
import sqlite3

from shared_code.csv_ops import CSV_ops
from layer_constructors.route_constructor import Route
from layer_constructors.stop_constructor import Stops
from layer_constructors.vehicle_constructor import Vehicle
from shared_code.from_sql import read_query

conn = sqlite3.connect("mbta_data.db")

route_type = 2
# 0/1 = heavy rail + light rail, 2 = commuter rail, 3 = bus, 4 = ferry
if route_type in [0, 1]:
    offset = 0 if route_type == 1 else 1
    vehicles = read_query(
        f"""SELECT * FROM (
            (SELECT * FROM vehicles_{route_type}
            UNION SELECT * FROM vehicles_{offset}) as vehicles
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type}
            UNION SELECT route_id, route_name, description from routes_{offset}) as routes 
            ON vehicles.route_id = routes.route_id);""",
        conn,
    )
    stops = read_query(
        f"""SELECT *, MAX(platform_code) as platform_code
            FROM (SELECT * FROM stops_{route_type} 
            UNION SELECT * FROM stops_{offset})
            GROUP BY parent_station;""",
        conn,
    )
    shapes = read_query(
        f"""SELECT * FROM (
            SELECT * FROM (
            (SELECT * FROM shapes_{route_type}
            UNION SELECT * FROM shapes_{offset})as shapes
            LEFT JOIN 
            (SELECT route_id, route_name, description from routes_{route_type} 
            UNION SELECT route_id, route_name, description from routes_{offset}) as routes 
            ON shapes.route_id = routes.route_id));""",
        conn,
    )
    predictions = read_query(
        f"""SELECT * FROM (
            (SELECT * FROM predictions_{route_type}  
            UNION SELECT * FROM predictions_{offset})as prd 
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type} 
            UNION SELECT route_id, route_name, description from routes_{offset}) as routes 
            ON prd.route_id = routes.route_id);""",
        conn,
    )
    alerts = read_query(
        f"""SELECT * FROM (SELECT * FROM (
            (SELECT * FROM alerts_{route_type} UNION SELECT * FROM alerts_{offset})  as alerts 
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type} 
            UNION SELECT route_id, route_name, description from routes_{offset}) as routes 
            ON alerts.route_id == routes.route_id));""",
        conn,
    )
else:
    vehicles = read_query(
        f"""SELECT * FROM (
            SELECT * FROM vehicles_{route_type} as vehicles 
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type}) as routes 
            ON vehicles.route_id = routes.route_id);""",
        conn,
    )
    stops = read_query(
        f"""SELECT *, MAX(platform_code) as platform_code
            FROM stops_{route_type}
            GROUP BY parent_station;""",
        conn,
    )
    shapes = read_query(
        f"""SELECT * FROM (SELECT * FROM shapes_{route_type} as shapes
            LEFT JOIN 
            (SELECT route_id, route_name, description from routes_{route_type}) as routes 
            ON shapes.route_id = routes.route_id) 
            ORDER BY shape_id desc;""",
        conn,
    )
    predictions = read_query(
        f"""SELECT * FROM (
            SELECT * FROM predictions_{route_type}  as prd 
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type}) as routes 
            ON prd.route_id = routes.route_id);""",
        conn,
    )
    alerts = read_query(
        f"""SELECT * FROM (
            SELECT * FROM alerts_{route_type}  as alerts 
            LEFT JOIN (
            SELECT route_id, route_name, description from routes_{route_type}) as routes 
            ON alerts.route_id == routes.route_id);""",
        conn,
    )

if route_type == 2:
    zoom = 9.5
else:
    zoom = 12

system_map = folium.Map(
    location=geocoder.ip("me").latlng,
    tiles=None,
    zoom_start=zoom,
)

folium.TileLayer(
    tiles="cartodbdark_matter",  # tiles="cartodbpositron",
    control=False,
    min_zoom=9.5,
    min_lat=40,
    max_lat=44,
    min_lon=-73,
    max_lon=-69,
).add_to(system_map)

if not shapes.empty:
    route_time = time.time()
    shapes_layer = folium.FeatureGroup(name="shapes", show=True).add_to(system_map)

    if route_type != 3:
        bus_replacement_layer = folium.FeatureGroup(
            name="Bus Replacements", show=True
        ).add_to(system_map)

    for index, row in shapes.iterrows():
        try:
            al_df = alerts.loc[
                (alerts["route_id"] == row["route_id"])
                & (alerts["stop_id"].isnull())
                & (alerts["trip_id"].isnull())
            ]
        except KeyError:
            al_df = pd.DataFrame()
        if row["route_type"] == 3 and route_type != 3:
            Route(row, al_df).build_route().add_to(bus_replacement_layer)
        else:
            Route(row, al_df).build_route().add_to(shapes_layer)

    print(f"Routes layer built in {time.time() - route_time} seconds")

if not stops.empty:
    stops_time = time.time()

    stops_layer = folium.FeatureGroup(
        name="Stops", show=(True if route_type != 3 else False)
    ).add_to(system_map)

    for index, row in stops.iterrows():
        try:
            prd_df = predictions.loc[
                predictions["parent_station"] == row["parent_station"]
            ]
            al_df = alerts.loc[(alerts["stop_id"] == row["parent_station"])]
        except KeyError:
            prd_df = pd.DataFrame()
            al_df = pd.DataFrame()

        Stops(row, prd_df, al_df).build_stop().add_to(stops_layer)

    print(f"Stops layer built in {time.time() - stops_time} seconds")

if not vehicles.empty:
    vehicle_cluster_time = time.time()
    vehicle_cluster = MarkerCluster(name="Vehicles", show=True).add_to(system_map)
    # vehicle_layer = folium.FeatureGroup(name="Vehicles", show=True).add_to(map)
    vehicle_icon = Image.open("icon.png")

    for index, row in vehicles.iterrows():
        try:
            prd_df = predictions.loc[predictions["vehicle_id"] == row["vehicle_id"]]
            al_df = alerts.loc[alerts["trip_id"] == row["trip_id"]]
        except KeyError:
            prd_df = pd.DataFrame()
            al_df = pd.DataFrame()
        Vehicle(row, prd_df, al_df, vehicle_icon).build_vehicle().add_to(
            vehicle_cluster
        )
        # marker.add_to(vehicle_layer)

    print(f"Vehicle layer built in {time.time() - vehicle_cluster_time} seconds")

layer_control = folium.LayerControl().add_to(system_map)

# system_map.save("index.html")
system_map.show_in_browser()
