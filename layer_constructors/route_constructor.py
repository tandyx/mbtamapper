from dataclasses import dataclass
import polyline
import folium
import pandas as pd


@dataclass
class Route:
    row: pd.Series = None
    alerts: pd.DataFrame = None

    def __post_init__(self):
        if self.row["description"]:
            opacity = 1
            description = self.row["description"]
        else:
            description = "Bus Replacement"
            opacity = 0.5

        rt = self.row.get("route_name")
        self.route_name = rt if rt and rt == rt else self.row["route_id"]

        self.line_color = self.row["route_color"]
        self.description = description
        self.opacity = opacity

    def build_route(self):
        """builds stop icon"""

        html = f"""
                    <strong>Route:</strong> {self.route_name}<br>
                    <strong>type:</strong> {self.description}<br>"""

        if not self.alerts.empty:
            html = (
                html
                + f"""<strong>Alerts: </strong> <br><a>{self.alerts.to_html()} </a><br>"""
            )
        if not self.alerts.empty:
            html = (
                html
                + f"""
                        <div class="hover-text">hover me
                        <span class="tooltip-text" id="fade">I'm a tooltip!</span>
                        </div>"""
            )

        popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)

        poly_line = folium.PolyLine(
            locations=polyline.decode(self.row["polyline"]),
            color="#" + self.row["route_color"],
            weight=1,
            opacity=self.opacity,
            popup=popup,
            tooltip=self.row["route_id"],
            zIndexOffset=-50,
        )

        return poly_line
