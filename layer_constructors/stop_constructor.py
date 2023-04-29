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
    def __post_init__(self):
        self.route_color = "FFFFFF"

    def build_stop(self):
        """constructs stop icon"""

        html = f"""
         <!DOCTYPE html>
            <html style = "color: #ffffff; font-family: Montserrat, sans-serif !important;">

            <head>
                <title>{self.row["parent_station"]}</title>
            </head>
            <body>
                <a href="https://www.mbta.com/stops/{self.row["parent_station"]}">
                <h1 style="color: #{self.route_color};margin: 0;">{self.row["stop_name"]}</h1>
                <h1 style="color: #{self.route_color};margin: 0;">{self.row["line_serviced"]}</h1>
                </a>"""
        if self.row["wheelchair_accessible"] == 1:
            html = html + """<a style="margin: 0;">Wheelchair Accessible</a></br>"""
        if not self.alerts.empty:
            html = html + f"""<a>Alerts: </br> {self.alerts.to_html()} </a><br>"""

        # TODO: add alerts tooltip
        # TODO: remote link underline

        popup = folium.Popup(folium.IFrame(html, width=500, height=500), max_width=500)
        stops_icon = folium.CustomIcon("mbta.png", icon_size=(17, 17))

        marker = folium.Marker(
            location=[self.row["latitude"], self.row["longitude"]],
            icon=stops_icon,
            popup=popup,
            tooltip=self.row["stop_name"],
            zIndexOffset=-25,
        )

        return marker
