
import folium
import branca.colormap as bcm

from folium.plugins import MarkerCluster

import geopandas as gpd

import pandas as pd

# Read in UK Historical Plaques data

plaques_df = pd.read_json("https://s3.eu-west-2.amazonaws.com/openplaques/open-plaques-United-Kingdom-2021-06-26.json").dropna().drop("updated_at", axis=1)

plaques = gpd.GeoDataFrame(

    plaques_df, geometry=gpd.points_from_xy(plaques_df.longitude, plaques_df.latitude, crs=4326)

)

plaques_df = None

# Read in London boroughs data

boroughs = gpd.read_file("https://skgrange.github.io/www/data/london_boroughs.json")

boroughs = boroughs.join(

            gpd.sjoin(plaques, boroughs).groupby("index_right").size().rename("numPlaques"),

            how="left",

        )

boroughs["area_sqkm"] = boroughs["area_hectares"] / 100

boroughs["PlaqueDensity_sqkm"] = boroughs["numPlaques"] / boroughs["area_sqkm"]

map = folium.Map(location=[42.3519, -71.0552], tiles="cartodbpositron", zoom_start=9)

title_html = """

             <h5 align=”center”; margin-bottom=0px; padding-bottom=0px; style=”font-size:20px”><b>Historical Plaques of London</b></h3>

             <h5 align=”center”; margin-top=0px; padding-top=0px; style=”font-size:14px”>Click on the blue circles for more info</h3>

                """
                
map.get_root().html.add_child(folium.Element(title_html))

marker_cluster = MarkerCluster().add_to(map)

for index, row in plaques.iterrows():

    html = f"""<strong>Title:</strong> {row["title"]}<br>

        <br>

        <strong>Inscription:</strong> {row["inscription"]}<br>

        <br>

        <strong>Erected:</strong> {row["erected_at"]}<br>

        <br>

        Find more info <a href={row["uri"]} target=”_blank”>here</a><br>

            “””

    iframe = folium.IFrame(html,

                       width=200,

                       height=200)

    popup = folium.Popup(iframe,

                     max_width=400)

    folium.CircleMarker(location=[row[“latitude”], row[“longitude”]],

                                         radius=10,

                                         color=“#3186cc”,

                                         fill=True, 

     fill_color=“#3186cc”,  

                                      popup=popup).add_to(marker_cluster)"""
                                      
                                      
# “Fall” color ramp from https://carto.com/carto-colors/

scale = (boroughs["PlaqueDensity_sqkm"].quantile((0, 0.02, 0.5, 0.9, 0.98, 1))).tolist()

colormap = bcm.LinearColormap(colors=["#008080","#70a494", "#b4c8a8", "#edbb8a", "#de8a5a","#ca562c"], 

    index=scale,

    vmin=min(boroughs["PlaqueDensity_sqkm"]),

    vmax=max(boroughs["PlaqueDensity_sqkm"]))

style_function = lambda x: {

    "fillColor": colormap(x["properties"]["PlaqueDensity_sqkm"]),

    "color": "black",

    "weight": 1.5,

    "fillOpacity": 0.3

}


folium.GeoJson(

    boroughs,

    style_function=style_function,

    tooltip=folium.GeoJsonTooltip(

        fields=["name", "numPlaques"],

        aliases=["Borough", "Historic Markers"],

        localize=True

    )

).add_to(map)

colormap.caption = "Historic markers per sq. km"

colormap.add_to(map)

map.save("map.html")

with open("UK-plaques-2021-06-26.json", "w") as outfile:

    outfile.write(plaques.to_json())

boroughs.to_file("london-boroughs.geojson", driver="GeoJSON") 