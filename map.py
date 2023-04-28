import time
import logging
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import numpy as np
import pandas as pd
import geocoder

from shared_code.csv_ops import CSV_ops
from layer_constructors.route_constructor import Route
from layer_constructors.stop_constructor import Stops
from layer_constructors.vehicle_constructor import Vehicle

route_type = 2
# 0/1 = heavy rail + light rail, 2 = commuter rail, 3 = bus, 4 = ferry
routes = pd.read_csv(CSV_ops("routes").get_second_latest())
stops = pd.read_csv(CSV_ops("stops").get_second_latest())
shapes = pd.read_csv(CSV_ops("shapes").get_second_latest())
vehicles = pd.read_csv(CSV_ops("vehicles").get_second_latest())
alerts = pd.read_csv(CSV_ops("alerts").get_second_latest())
predictions = pd.read_csv(CSV_ops("predictions").get_second_latest())

if route_type == 1 or route_type == 0:
    if not routes.empty:
        routes = routes.loc[routes["route_type"].isin([0, 1])]
    if not stops.empty:
        stops = stops.loc[stops["route_type"].isin([0, 1])]
    if not shapes.empty:
        shapes = shapes.loc[shapes["parent_route_type"].isin([0, 1])]
    if not vehicles.empty:
        vehicles = vehicles.loc[vehicles["route_type"].isin([0, 1])]
    if not alerts.empty:
        alerts = alerts.loc[alerts["route_type"].isin([0, 1])]
    if not predictions.empty:
        predictions = predictions.loc[predictions["route_type"].isin([0, 1])]
else:
    if not routes.empty:
        routes = routes.loc[routes["route_type"] == route_type]
    if not stops.empty:
        stops = stops.loc[stops["route_type"] == route_type]
    if not shapes.empty:
        shapes = shapes.loc[shapes["parent_route_type"] == route_type]
    if not vehicles.empty:
        vehicles = vehicles.loc[vehicles["route_type"] == route_type]
    if not alerts.empty:
        alerts = alerts.loc[alerts["route_type"] == route_type]
    if not predictions.empty:
        predictions = predictions.loc[predictions["route_type"] == route_type]

if route_type == 2:
    zoom = 9.5
else:
    zoom = 12

if not stops.empty:
    stops = stops.drop_duplicates("parent_station")
if not predictions.empty:
    predictions = pd.merge(predictions, routes, how="left")
if not shapes.empty:
    shapes = pd.merge(shapes, routes, how="left").sort_index(ascending=False)
if not vehicles.empty:
    vehicles = pd.merge(vehicles, routes, how="left")


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

system_map.save("index.html")
system_map.show_in_browser()
