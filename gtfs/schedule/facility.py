"""File to hold the Facility class and its associated methods."""
from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, String, Float
from ..base import GTFSBase

# pylint: disable=line-too-long


class Facility(GTFSBase):
    """Facilities"""

    __tablename__ = "facilities"
    __filename__ = "facilities.txt"

    facility_id = Column(String, primary_key=True)
    facility_code = Column(String)
    facility_class = Column(String)
    facility_type = Column(String)
    stop_id = Column(
        String,
        ForeignKey("stops.stop_id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    facility_short_name = Column(String)
    facility_long_name = Column(String)
    facility_desc = Column(String)
    facility_lat = Column(Float)
    facility_lon = Column(Float)
    wheelchair_facility = Column(String)

    facility_properties = relationship(
        "FacilityProperty", back_populates="facility", passive_deletes=True
    )

    stop = relationship("Stop", back_populates="facilities")

    ACCENT_COLOR = "#007ebb"

    def __repr__(self) -> str:
        return f"<Facilities(facility_id={self.facility_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the facility

        Returns:
            Point: shapely Point object of the facility
        """
        return Point(self.facility_lon, self.facility_lat)

    def as_feature(self) -> Feature:
        """Returns facility object as a feature.

        Returns:
            Feature: facility as a feature.
        """

        point = self.as_point()
        if point == self.stop.as_point():
            point = Point(self.facility_lon + 0.001, self.facility_lat + 0.001)

        return Feature(
            id=self.facility_id,
            geometry=point,
            properties={
                "popupContent": self.as_html_popup(),
                "name": self.facility_long_name or self.facility_short_name,
            },
        )

    def as_html_row(self, parking: bool = True) -> str:
        """Returns facility object as a html string.

        Args:
            parking (bool, optional): Whether to return parking facilities. Defaults to True.
        Returns:
            str: facility as a html string.
        """

        return (
            "<tr>"
            f"<td>{self.facility_long_name}</td>"
            f"<td>{self.return_formatted_capacity()}</td>"
            f"{('<td>' + self.return_property('fee-daily', 'Unknown') + '</td>') if parking else ''}"
            f"{('<td>' + self.return_formatted_payment_app('') + '</td>') if parking else ''}"
            "</tr>"
        )

    def as_html_popup(self) -> str:
        """Returns facility object as a html string.

        Returns:
            str: facility as a html string.
        """
        contact_url = self.return_property("contact-url")
        owner = self.return_property("owner", "Unknown")
        daily_rate = self.return_property("fee-daily")
        monthly_rate = self.return_property("fee-monthly")
        payment_app_html = self.return_formatted_payment_app()
        header_html = (
            f"<a href = '{contact_url}' target='_blank' class = 'facility_header';'>{self.facility_long_name}</a></br>"
            if contact_url
            else f"<a class = 'facility_header'>{self.facility_long_name}</a></br>"
        )

        daily_rate_html = f"Daily Rate: {daily_rate}</br>" if daily_rate else ""
        monthly_rate_html = f"Monthly Rate: {monthly_rate}</br>" if monthly_rate else ""

        contact_html = (
            f"Contact: <a href = '{contact_url}' target='_blank' class = 'facility_contact'>{self.return_property('contact', 'Unknown')}</a><span class='popup_footer'> ({self.return_property('contact-phone')})</span></br>"
            if contact_url
            else ""
        )
        acessible_spots = int(self.return_property("capacity-accessible", 0))
        wheelchair = (
            """<div class = "tooltip-mini_image" onmouseover="hoverImage('whImg')" onmouseleave="unhoverImage('whImg')">"""
            """<img src="static/img/wheelchair.png" alt="accessible" class="mini_image" id="whImg">"""
            f"""<span class="tooltiptext-mini_image">Accessible spots: {acessible_spots}</span></div></br>"""
            if acessible_spots
            else ""
        )

        return (
            f"{header_html}"
            f"<body>"
            f"{owner if owner not in ['City/Town', 'Unknown', 'Private'] else self.return_property('operator', owner)}</br>"
            f"—————————————————————————————————</br>"
            f"{wheelchair}"
            f"Capacity: {self.return_property('capacity', 'Unknown')} </br>"
            f"{('Payment App: ' + payment_app_html) if payment_app_html else ''}"
            f"{daily_rate_html}"
            f"{monthly_rate_html}"
            f"<span class='popup_footer'>"
            f"{contact_html}"
            f"Overnight Parking: {self.return_property('overnight-allowed', 'Unknown')}</br>"
            "</span></body>"
        )

    def return_property(self, property_id: str, default: str = "") -> str:
        """Returns facility object as a html string.

        Args:
            property_id (str): The property_id to return.
            default (str, optional): The default value to return if the property_id is not found. Defaults to "".
        Returns:
            str: The value of the property_id.
        """
        return next(
            (
                fp.value
                for fp in self.facility_properties
                if fp.property_id == property_id
            ),
            default,
        )

    def return_formatted_payment_app(self, default: str = "") -> str:
        """Returns the payment app of the facility as a formatted string.

        Args:
            default (str, optional): The default value to return if the payment app is not found. Defaults to "".
        Returns:
            str: The payment app of the facility as a formatted string.
        """
        payment_app_url = self.return_property("payment-app-url")
        payment_app_id = self.return_property("payment-app-id")
        return (
            f"<a href = {payment_app_url} target='_blank' class='facility_accent';'>{self.return_property('payment-app', 'Unknown') }</a>{(f' - {payment_app_id}') if payment_app_id else ''}</br>"
            if payment_app_url
            else default
        )

    def return_formatted_capacity(self, default: str = "") -> str:
        """Returns the capacity of the facility as a formatted string.

        Args:
            default (str, optional): The default value to return if the capacity is not found. Defaults to "".
        Returns:
            str: The capacity of the facility as a formatted string.
        """
        accessible_spots = self.return_property("capacity-accessible")
        accessible_spots = (
            f"<span class='facility_accent'>({accessible_spots})</span>"
            if accessible_spots != ""
            else default
        )

        return self.return_property("capacity", "Unknown") + " " + accessible_spots
