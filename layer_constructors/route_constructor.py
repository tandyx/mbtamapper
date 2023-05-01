from dataclasses import dataclass
import polyline
import folium
import pandas as pd
from htmlelements import Popup


@dataclass
class Route:
    row: pd.Series = None
    alerts: pd.DataFrame = None

    def __post_init__(self):
        opacity = 0.5
        if self.row["description"] and self.row["description"] not in [
            "Local Bus",
            "Supplemental Bus",
        ]:
            opacity = 1
            description = self.row["description"]
        elif self.row["description"] in ["Local Bus", "Supplemental Bus"]:
            description = self.row["description"]
        else:
            description = "Bus Replacement"

        rt = self.row.get("route_name")
        self.route_name = rt if rt and rt == rt else self.row["route_id"]

        self.line_color = self.row["route_color"]
        self.description = description
        self.opacity = opacity

    def build_route(self):
        """builds stop icon"""

        html = f"""
         <!DOCTYPE html>   
            <html style = "color: #ffffff; font-family: Montserrat, sans-serif !important;">

            <head>
                <title>{self.route_name}</title>   

            </head>
            <body>
                <a href="https://www.mbta.com/schedules/{self.row["route_id"]}"> 
                <h1 style="color: #{self.row["route_color"]};margin: 0;">{self.route_name}</h1>
                </a>
                <a style="margin: 0;">{self.description}</a></br>"""

        # TODO: add alerts tooltip
        # TODO: remote link underline
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

        html = html + "</body></html>"
        popup = folium.Popup(
            folium.IFrame(html, width=500, height=500),
            max_width=500,
        ).add_child(folium.CssLink("popup.css"))
        css = folium.CssLink("popup.css").add_to(popup)

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
