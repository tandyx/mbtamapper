import time
import logging
import folium
from folium.plugins import MarkerCluster
from PIL import Image
import geopandas as gpd
import numpy as np
import pandas as pd
import geocoder


from vehicles import getvehicles
from routes import import_mbta_shapes
from stops import getstops
from layer_constructors.route_constructor import Route
from layer_constructors.stop_constructor import Stops
from layer_constructors.vehicle_constructor import Vehicle

vehicle_type = 1

vehicles = getvehicles(vehicle_type)
routes = import_mbta_shapes(vehicle_type)
stops = getstops(vehicle_type)

zoom = 14

if vehicle_type == 0:
    vehicles = pd.concat([vehicles, getvehicles(1)])
    routes = pd.concat([routes, import_mbta_shapes(1)])
    stops = pd.concat([stops, getstops(1)])
elif vehicle_type == 1:
    vehicles = pd.concat([vehicles, getvehicles(0)])
    routes = pd.concat([routes, import_mbta_shapes(0)])
    stops = pd.concat([stops, getstops(0)])
elif vehicle_type == 2:
    zoom = 9.5

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

route_time = time.time()
routes_layer = folium.FeatureGroup(name="Routes", show=True).add_to(system_map)
for index, row in routes.iterrows():
    Route(row).build_route().add_to(routes_layer)
print(f"Routes layer built in {time.time() - route_time} seconds")

stops_time = time.time()
stops_layer = folium.FeatureGroup(
    name="Stops", show=(True if vehicle_type != 3 else False)
).add_to(system_map)
for index, row in stops.iterrows():
    Stops(row).build_stop().add_to(stops_layer)
print(f"Stops layer built in {time.time() - stops_time} seconds")

vehicle_cluster_time = time.time()
vehicle_cluster = MarkerCluster(name="Vehicles", show=True).add_to(system_map)
# vehicle_layer = folium.FeatureGroup(name="Vehicles", show=True).add_to(map)
vehicle_icon = Image.open("icon.png")
for index, row in vehicles.iterrows():
    Vehicle(row, vehicle_icon).build_vehicle().add_to(vehicle_cluster)
    # marker.add_to(vehicle_layer)
print(f"Vehicle layer built in {time.time() - vehicle_cluster_time} seconds")

layer_control = folium.LayerControl().add_to(system_map)

system_map.save("index.html")
system_map.show_in_browser()
