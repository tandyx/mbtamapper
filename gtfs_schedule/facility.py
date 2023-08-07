"""File to hold the Calendar class and its associated methods."""
from geojson import Feature
from shapely.geometry import Point
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Column, String, Float
from gtfs_loader.gtfs_base import GTFSBase

# pylint: disable=line-too-long


class Facility(GTFSBase):
    """Facilities"""

    __tablename__ = "facilities"

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

    ACCENT_COLOR = "#4086f7"

    def __repr__(self) -> str:
        return f"<Facilities(facility_id={self.facility_id})>"

    def as_point(self) -> Point:
        """Returns a shapely Point object of the facility"""
        return Point(self.facility_lon, self.facility_lat)

    def as_feature(self) -> Feature:
        """Returns facility object as a feature."""

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
        """Returns facility object as a html string."""

        return (
            "<tr>"
            f"<td>{self.facility_long_name}</td>"
            f"<td>{self.return_formatted_capacity()}</td>"
            f"{('<td>' + self.return_property('fee-daily', 'Unknown') + '</td>') if parking else ''}"
            "</tr>"
        )

    def as_html_popup(self) -> str:
        """Returns facility object as a html string."""
        contact_url = self.return_property("contact-url")
        owner = self.return_property("owner", "Unknown")

        return (
            f"<a href = '{contact_url}' target='_blank' style='font-size:28pt;text-decoration: none;text-align: left;color:{Facility.ACCENT_COLOR};'>{self.facility_long_name}</a></br>"
            f"<body style='color:#ffffff;text-align: left;'>"
            f"{owner if owner not in ['City/Town', 'Unknown'] else self.return_property('operator', owner)}</br>"
            f"—————————————————————————————————</br>"
            f"Capacity: {self.return_formatted_capacity()} </br>"
            f"Payment App: <a href = {self.return_property('payment-app-url')} target='_blank' style='text-decoration: none;color:{Facility.ACCENT_COLOR};'>{self.return_property('payment-app', 'Unknown')}</a></br>"
            f"Daily Rate: {self.return_property('fee-daily', 'Unknown')}</br>"
            f"Monthly Rate: {self.return_property('fee-monthly', 'Unknown')}</br>"
            f"<a style='color:grey;font-size:9pt'>"
            f"Contact: <a href = '{contact_url}' target='_blank' style='text-decoration: none;color:{Facility.ACCENT_COLOR};font-size:9pt'>{self.return_property('contact', 'Unknown')}</a><a style='color:grey;font-size:9pt'> ({self.return_property('contact-phone')})</a></br>"
            f"<a style='color:grey;font-size:9pt'>Overnight Parking: {self.return_property('overnight-allowed', 'Unknown')}</a></br>"
            "</a></body>"
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

    def return_formatted_capacity(self) -> str:
        """Returns the capacity of the facility as a formatted string.

        Returns:
            str: The capacity of the facility as a formatted string.
        """
        accessible_spots = self.return_property("capacity-accessible")
        accessible_spots = (
            f"<a style='color:{Facility.ACCENT_COLOR};'>({accessible_spots})</a>"
            if accessible_spots != ""
            else ""
        )

        return self.return_property("capacity", "Unknown") + " " + accessible_spots
