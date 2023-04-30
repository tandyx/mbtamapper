import time
import logging
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import numpy as np
import pandas as pd
import geocoder
import sqlite3
import streamlit as st
from streamlit_folium import st_folium, folium_static

from shared_code.csv_ops import CSV_ops
from shared_code.from_sql import GrabData
from layer_constructors.route_constructor import Route
from layer_constructors.stop_constructor import Stops
from layer_constructors.vehicle_constructor import Vehicle

# TODO: split silver line and bus lines into their own layers

conn = sqlite3.connect("mbta_data.db")
start_time = time.time()
# 0/1 = heavy rail + light rail, 2 = commuter rail, 3 = bus, 4 = ferry
route_type = 2

vehicles = GrabData(route_type, conn).grabvehicles()
stops = GrabData(route_type, conn).grabstops()
shapes = GrabData(route_type, conn).grabshapes()
predictions = GrabData(route_type, conn).grabpredictions()
alerts = GrabData(route_type, conn).grabalerts()


zoom = 9.5 if route_type == 2 else 12

system_map = folium.Map(
    location=geocoder.ip("me").latlng,
    tiles=None,
    zoom_start=zoom,
)
system_map.get_root().title = "MBTA System Map"
html_to_insert = """<style>.leaflet-popup-content-wrapper, .leaflet-popup-tip
                    {
                        background: rgb(0, 0, 0, 0.95) !important;
                    }
                    </style>
                    <link rel="icon" href = "mbta.png" />"""

system_map.get_root().header.add_child(folium.Element(html_to_insert))


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

    vehicle_cluster = MarkerCluster(
        name="Vehicles",
        show=True,
    ).add_to(system_map)
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

# system_map.keep_in_front(lambda item: item in vehicle_cluster)
system_map.save("index.html")
system_map.show_in_browser()

# # st_data = folium_static(system_map, width=1000, height=800)
# st_data = st_folium(
#     system_map, width=1000, height=1000, feature_group_to_add=vehicle_cluster
# )
print(f"Map built in {time.time() - start_time} seconds")
