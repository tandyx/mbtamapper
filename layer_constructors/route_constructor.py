from dataclasses import dataclass
import polyline
import folium
import pandas as pd


@dataclass
class Route:
    row: pd.Series = None
    alerts: pd.DataFrame = None

    def __post_init__(self):
        opacity = 1
        if self.row["route_type"] == 4:
            vehicle_type = "Ferry"
        if self.row["route_type"] == 3:
            vehicle_type = "Shuttle"
            opacity = 0.5
        elif self.row["route_type"] == 2:
            vehicle_type = "Commuter Rail"
        elif self.row["route_type"] == 1:
            vehicle_type = "Heavy Rail"
        elif self.row["route_type"] == 0:
            vehicle_type = "Light Rail"

        rt = self.row.get("route_name")
        self.route_name = rt if rt and rt == rt else self.row["route_id"]

        self.line_color = self.row["route_color"]
        self.vehicle_type = vehicle_type
        self.opacity = opacity

    def build_route(self):
        """builds stop icon"""

        html = f"""<strong>Route:</strong> {self.route_name}<br>
                    <strong>type:</strong> {self.vehicle_type}<br>"""

        if not self.alerts.empty:
            html = (
                html
                + f"""<strong>Alerts: </strong> <br><a>{self.alerts.to_html()} </a><br>"""
            )

        popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)

        poly_line = folium.PolyLine(
            locations=polyline.decode(self.row["polyline"]),
            color="#" + self.row["route_color"],
            weight=1,
            opacity=self.opacity,
            popup=popup,
            tooltip=self.row["route_id"],
        )

        return poly_line
