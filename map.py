
import folium
import branca.colormap as bcm

from folium.plugins import MarkerCluster

import geopandas as gpd

import pandas as pd

from vehicles import getvehicles

# Read in UK Historical Plaques data

vehicles = getvehicles()

map = folium.Map(location=[42.3519, -71.0552], tiles="cartodbpositron", zoom_start=9)

title_html = """

             <h5 align="center"; margin-bottom=0px; padding-bottom=0px; style="font-size:20px"><b>Historical Plaques of London</b></h3>

             <h5 align="center"; margin-top=0px; padding-top=0px; style="font-size:14px">Click on the blue circles for more info</h3>

                """
                
map.get_root().html.add_child(folium.Element(title_html))

marker_cluster = MarkerCluster().add_to(map)

for index, row in vehicles.iterrows():

    # html = f"""<strong>Title:</strong> {row["vehicle_id"]}<br>

    #     <br>

    #     <strong>Inscription:</strong> {row["inscription"]}<br>

    #     <br>

    #     <strong>Erected:</strong> {row["erected_at"]}<br>

    #     <br>

    #     Find more info <a href={row["uri"]} target="_blank">here</a><br>

    #         """
    
    html = f"""<strong>Title:</strong> {row["vehicle_id"]}<br>"""

    iframe = folium.IFrame(html,width=200,height=200)

    popup = folium.Popup(iframe,max_width=400)
    

    folium.CircleMarker(location=[row["latitude"], row["longitude"]], radius=10,color="#3186cc", fill=True, zfill_color="#3186cc",  popup=popup, angle=34).add_to(marker_cluster)
                                      
                                      
# "Fall" color ramp from https://carto.com/carto-colors/

map.save("map.html")

with open("vehicles.json", "w") as outfile:
    outfile.write(vehicles.to_json())

