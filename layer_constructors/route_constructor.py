from dataclasses import dataclass
import polyline
import folium
import pandas as pd


@dataclass
class Route:
    row: pd.Series = None

    def __post_init__(self):
        opacity = 1
        if self.row["MBTARouteType"] == 4:
            vehicle_type = "Ferry"
        if self.row["MBTARouteType"] == 3:
            vehicle_type = "Shuttle"
            opacity = 0.5
        elif self.row["MBTARouteType"] == 2:
            vehicle_type = "Commuter Rail"
        elif self.row["MBTARouteType"] == 1:
            vehicle_type = "Heavy Rail"
        elif self.row["MBTARouteType"] == 0:
            vehicle_type = "Light Rail"

        self.line_color = self.row["MBTAColor"]
        self.vehicle_type = vehicle_type
        self.opacity = opacity

    def build_route(self):
        """builds stop icon"""

        html = f"""<strong>Route:</strong> {self.row["MBTARoute"]}<br>
                    <strong>type:</strong> {self.vehicle_type}<br>"""

        popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)

        poly_line = folium.PolyLine(
            locations=polyline.decode(self.row["MBTAPolyLine"]),
            color="#" + self.row["MBTAColor"],
            weight=1,
            opacity=self.opacity,
            popup=popup,
            tooltip=self.row["MBTARoute"],
        )

        return poly_line
