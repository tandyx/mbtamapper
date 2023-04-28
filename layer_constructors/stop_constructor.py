from dataclasses import dataclass
import folium
import pandas as pd


@dataclass
class Stops:
    row: pd.Series = None
    predictions: pd.DataFrame = None
    alerts: pd.DataFrame = None

    # def __post_init__(self):
    #     if self.row["wheelchair_accessible"] == 1:
    #         acessible = True
    #     else:
    #         acessible = False
    #     self.acessible = acessible

    def build_stop(self):
        """constructs stop icon"""

        html = f"""<strong>Stop:</strong> <a href="https://www.mbta.com/stops/{self.row["parent_station"]}">{self.row["stop_name"]}</a><br>"""

        if self.row["wheelchair_accessible"] == 1:
            html = html + """<a>Wheelchair Accessible</a><br> """
        if not self.alerts.empty:
            html = (
                html
                + f"""<strong>Alerts: </strong> <br><a>{self.alerts.to_html()} </a><br>"""
            )

        popup = folium.Popup(folium.IFrame(html, width=200, height=200), max_width=400)
        stops_icon = folium.CustomIcon("mbta.png", icon_size=(17, 17))

        marker = folium.Marker(
            location=[self.row["latitude"], self.row["longitude"]],
            icon=stops_icon,
            popup=popup,
            tooltip=self.row["stop_name"],
            zIndexOffset=-25,
        )

        return marker
