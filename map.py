import time
import logging
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import numpy as np
import pandas as pd
import geocoder

from shared_code.csv_ops import CSV_ops

from vehicles import getvehicles
from shapes import getshapes
from stops import getstops
from routes import getroutes
from predictions import getpredictions
from alerts import getalerts
from layer_constructors.route_constructor import Route
from layer_constructors.stop_constructor import Stops
from layer_constructors.vehicle_constructor import Vehicle

vehicle_type = 2
# 0 = light rail, 1 = heavy rail + light rail, 2 = commuter rail, 3 = bus, 4 = ferry
routes = getroutes(vehicle_type).to_hdf("data/routes.h5", key="routes")
active_routes = ",".join(routes["route_id"].unique().tolist())

vehicles = getvehicles(vehicle_type)
shapes = getshapes(vehicle_type, active_routes)
stops = getstops(vehicle_type)
predictions = getpredictions(vehicle_type, active_routes)
alerts = getalerts(vehicle_type)


zoom = 14
if vehicle_type == 1:
    routes0 = getroutes(0)
    active_routes0 = ",".join(routes0["route_id"].unique().tolist())

    routes = pd.concat([routes, routes0])
    predictions = pd.concat([predictions, getpredictions(0, active_routes0)])
    vehicles = pd.concat([vehicles, getvehicles(0)])
    shapes = pd.concat([shapes, getshapes(0, active_routes0)])
    stops = pd.concat([stops, getstops(0)])
    alerts = pd.concat([alerts, getalerts(0)])

elif vehicle_type == 2:
    zoom = 9.5

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

    if vehicle_type != 3:
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
        if row["route_type"] == 3 and vehicle_type != 3:
            Route(row, al_df).build_route().add_to(bus_replacement_layer)
        else:
            Route(row, al_df).build_route().add_to(shapes_layer)

    print(f"Routes layer built in {time.time() - route_time} seconds")

if not stops.empty:
    stops_time = time.time()

    stops_layer = folium.FeatureGroup(
        name="Stops", show=(True if vehicle_type != 3 else False)
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
