from dataclasses import dataclass
import time
import folium
from PIL import Image, ImageFont
import numpy as np
import pandas as pd
from shared_code import center_text
from htmlelements import Popup


@dataclass
class Vehicle:
    row: pd.Series = None
    predictions: pd.DataFrame = None
    alerts: pd.DataFrame = None
    vehicle_icon: Image.Image = None

    def __post_init__(self):
        if self.row["stop_status"] == "IN_TRANSIT_TO":
            status = "In transit to"
        elif self.row["stop_status"] == "STOPPED_AT":
            status = "Stopped at"
        else:
            status = "Unknown to"

        self.status = status

        if (
            self.row["trip_short_name"] == self.row["trip_short_name"]
            and self.row["trip_short_name"]
        ):
            self.trip_name = self.row["trip_short_name"]
        else:
            self.trip_name = self.row["trip_id"]

        if self.row["speed"] == self.row["speed"] and self.row["speed"]:
            self.speed = str(round(self.row["speed"] * 2.23694, 2)) + " mph"
        else:
            self.speed = "unknown"

    def build_vehicle(self):
        """builds vehicle icon"""

        html = f"""
         <!DOCTYPE html>   
            <html style = "color: #ffffff; font-family: Montserrat, sans-serif !important;">

            <head>
                <title>{self.row["vehicle_id"]}</title>   
            </head>
            <body>
                <a href="https://www.mbta.com/schedules/{self.row["route_id"]}"> 
                <h1 style="color: #{self.row["route_color"]};margin: 0;">{self.trip_name}</h1>
                </a>
                <a style="margin: 0;">{self.row["vehicle_id"]}</a></br>"""

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

            html = html + f"""<a margin: 0;"> {alert_popup} </a>"""

        html = (
            html
            + f"""
                <br><a style="margin: 0;">{self.row["route_name"]}</a></br>
                <a style="margin: 0;"> {self.status} <a href="https://www.mbta.com/stops/{self.row["parent_station"]}">{self.row["stop_name"]}</a><br>
                <a style="margin: 0;"> timestamp: {self.row["timestamp"]}</a><br>
                <a style="margin: 0;"> speed: {self.speed}</a><br>
                <a style="margin: 0;"> bearing: {self.row["bearing"]} degrees </a><br>"""
        )
        # TODO: add alerts tooltip

        # for alert in alerts:
        #     html = html + f"""<a href="https://www.mbta.com/alerts/{alert}">{alert}</a><br>"""

        popup = folium.Popup(folium.IFrame(html, width=400, height=400))

        # don't even think about it

        icon = folium.CustomIcon(self.generate_icon(), icon_size=(50, 50))

        marker = folium.Marker(
            location=[self.row["latitude"], self.row["longitude"]],
            icon=icon,
            popup=popup,
            zIndexOffset=1000,
            tooltip=self.row["vehicle_id"],
        )
        return marker

    def generate_icon(self):
        """generates vehicle icon"""

        vehicle_image = self.vehicle_icon.rotate(-1 * self.row["bearing"])

        center_text.center_text(
            vehicle_image,
            ImageFont.truetype("montserrat.ttf", 200),
            self.row["trip_short_name"],
            "#ffffff",
            (0, -40),
        )

        vehicle_image = np.array(vehicle_image)

        return vehicle_image
