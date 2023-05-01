from dataclasses import dataclass
import folium
import pandas as pd
from htmlelements import Popup


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
        if self.row["line_serviced"] == "Commuter Rail":
            self.route_color = "80276C"
        elif self.row["line_serviced"] == "Green Line":
            self.route_color = "00843D"
        elif self.row["line_serviced"] == "Orange Line":
            self.route_color = "ED8B00"
        elif self.row["line_serviced"] in ["Red Line", "Mattapan Trolley"]:
            self.route_color = "DA291C"
        elif self.row["line_serviced"] == "Blue Line":
            self.route_color = "003DA5"
        elif self.row["line_serviced"] == "Silver Line":
            self.route_color = "7C878E"
        elif self.row["line_serviced"] == "Bus Line":
            self.route_color = "FFC72C"
        elif self.row["line_serviced"][-5:] == "Ferry":
            self.route_color = "008EAA"
        else:
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
                </a>"""
        if (
            self.row["line_serviced"]
            and self.row["line_serviced"] == self.row["line_serviced"]
        ):
            html = (
                html
                + f"""<a style=";margin: 0;">{self.row["line_serviced"]}</a></br>"""
            )
        if self.row["wheelchair_accessible"] == 1:
            wheelchair_popup = Popup(
                "wheelchair.png",
                "Wheelchair Accessible",
                "20",
                "20",
                "Wheelchair Accessible",
            ).popup()
            html = html + f"""<a>{wheelchair_popup}</a>"""
        if not self.alerts.empty:
            alert = (
                self.alerts[["header", "effect", "link", "start_time", "end_time"]]
                .drop_duplicates()
                .reset_index(drop=True)
                .style.set_properties(
                    **{
                        "background-color": "black",
                        "font-size": "7pt",
                    }
                )
                .to_html(
                    index=False,
                    sparse_index=False,
                )
            )
            alert_popup = Popup(
                "alert.png",
                "Alerts",
                "20",
                "20",
                alert,
            ).popup()
            html = html + f"""<a style="margin:0px"> {alert_popup} </a><br>"""

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
