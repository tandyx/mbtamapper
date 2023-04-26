import folium
import time
import logging
from folium.plugins import MarkerCluster
from PIL import Image, ImageFont
from base64 import b64encode
import polyline
import geopandas as gpd
import numpy as np
import pandas as pd


from vehicles import getvehicles
from routes import import_mbta_shapes
from stops import getstops
from shared_code import center_text

# Read in UK Historical Plaques data


vehicles = getvehicles(2)
routes = import_mbta_shapes(2)
stops = getstops(2)

map = folium.Map(
    location=[42.3519, -71.0552],
    tiles="cartodbpositron",
    zoom_start=9,
)

routes_layer = folium.FeatureGroup(name="Routes", show=True).add_to(map)

for index, row in routes.iterrows():
    if row["MBTARouteType"] == 3:
        line_color = "black"
        vehicle_type = "shuttle"
        pass
    else:
        line_color = "purple"
        vehicle_type = "heavy_rail"

        html = f"""<strong>Route:</strong> {row["MBTARoute"]}<br>
                <strong>type:</strong> {vehicle_type}<br>"""
        popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)

        folium.PolyLine(
            locations=polyline.decode(row["MBTAPolyLine"]),
            color=line_color,
            weight=1,
            opacity=1,
            popup=popup,
        ).add_to(routes_layer)


stops_layer = folium.FeatureGroup(name="Stops", show=True).add_to(map)

for index, row in stops.iterrows():
    if row["wheelchair_accessible"] == 1:
        acessible = "True"
    elif row["wheelchair_accessible"] == 2:
        acessible = "False"
    else:
        acessible = "Unknown"

    html = f"""<strong>Stop:</strong> <a href="https://www.mbta.com/stops/{row["parent_station"]}">{row["stop_name"]}</a><br>
               <strong>Platform:</strong> {row["platform_code"]}<br> 
               <strong>Wheelchair Accessible:</strong> {acessible}<br>"""

    popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)
    stops_icon = folium.CustomIcon("mbta.png", icon_size=(17, 17))

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=stops_icon,
        popup=popup,
    ).add_to(stops_layer)


# vehicle_cluster = MarkerCluster().add_to(map)
vehicle_layer = folium.FeatureGroup(name="Vehicles", show=True).add_to(map)

for index, row in vehicles.iterrows():
    html = f"""<strong>Vehicle:</strong> {row["vehicle_id"]}<br>
               <strong>Trip:</strong> {row["trip_short_name"]}<br> 
               <strong>Route:</strong> {row["route"]}<br>
               <strong>Status:</strong> {row["stop_status"]} <a href="https://www.mbta.com/stops/{row["parent_station"]}">{row["stop_name"]}</a><br>
               <strong>Time:</strong> {row["timestamp"]}<br>
               <strong>Speed:</strong> {row["speed"]} mph<br>
               <strong>Heading:</strong> {row["bearing"]} degrees<br>"""

    iframe = folium.IFrame(html, width=200, height=200)
    popup = folium.Popup(iframe, max_width=400)

    # don't even think about it
    start = time.time()
    img = Image.open("icon.png").rotate(-1 * row["bearing"])

    center_text.center_text(
        img,
        ImageFont.truetype("times", 275),
        row["trip_short_name"],
        (0, 0, 0),
        (0, -40),
    )

    icon = folium.CustomIcon(np.array(img), icon_size=(50, 50))

    print("Icon rotation took %s seconds", time.time() - start)

    marker = folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=icon,
        popup=popup,
        zIndexOffset=1000,
    )

    # marker.add_to(vehicle_cluster)
    marker.add_to(vehicle_layer)

layer_control = folium.LayerControl().add_to(map)
# title_html =
# <head>
#     <title>Test</title>
#     <style>h1 { background-color: #000000; opacity: 0.8; overflow: hidden; }</style>
# </head>
# <body>
#     <h1>Big Text</h1>
# </body>
#             """

# map.get_root().html.add_child(folium.Element(css.inline(title_html)))


# "Fall" color ramp from https://carto.com/carto-colors/
map.save("index.html")
map.show_in_browser()

with open("vehicles.json", "w") as outfile:
    outfile.write(vehicles.to_json())
