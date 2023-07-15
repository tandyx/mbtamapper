"""Alerts"""
import os
import logging
import requests
import pandas as pd
import numpy as np
from dateutil.parser import isoparse

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship, reconstructor, Session
from sqlalchemy.exc import IntegrityError

from gtfs_loader.gtfs_base import GTFSBase
from shared_code.df_unpack import df_unpack
from shared_code.to_sql import to_sql_excpetion

RENAME_DICT = {
    "id": "alert_id",
    "type": "alert_type",
    "attributes_banner": "banner",
    "attributes_cause": "cause",
    "attributes_created_at": "created_at",
    "attributes_description": "description",
    "attributes_effect": "effect",
    "attributes_header": "header",
    "attributes_lifecycle": "lifecycle",
    "attributes_service_effect": "service_effect",
    "attributes_severity": "severity",
    "attributes_short_header": "short_header",
    "attributes_timeframe": "timeframe",
    "attributes_updated_at": "updated_at",
    "attributes_url": "url",
    "links_self": "links_self",
    "attributes_active_period_end": "active_period_end",
    "attributes_active_period_start": "active_period_start",
    "attributes_informed_entity_direction_id": "direction_id",
    "attributes_informed_entity_route": "route_id",
    "attributes_informed_entity_route_type": "route_type",
    "attributes_informed_entity_trip": "trip_id",
    "attributes_informed_entity_stop": "stop_id",
}

UNPACK_LIST = ["attributes_active_period", "attributes_informed_entity"]


class Alert(GTFSBase):
    """Alerts"""

    __tablename__ = "alerts"

    alert_id = Column(String)
    alert_type = Column(String)
    banner = Column(String)
    cause = Column(String)
    created_at = Column(String)
    description = Column(String)
    effect = Column(String)
    header = Column(String)
    lifecycle = Column(String)
    service_effect = Column(String)
    severity = Column(Integer)
    short_header = Column(String)
    timeframe = Column(String)
    updated_at = Column(String)
    url = Column(String)
    links_self = Column(String)
    active_period_end = Column(String)
    active_period_start = Column(String)
    direction_id = Column(String)
    route_id = Column(String)
    route_type = Column(String)
    trip_id = Column(String)
    stop_id = Column(String)
    index = Column(Integer, primary_key=True)

    route = relationship(
        "Route",
        back_populates="alerts",
        primaryjoin="foreign(Alert.route_id)==Route.route_id",
        viewonly=True,
    )
    trip = relationship(
        "Trip",
        back_populates="alerts",
        primaryjoin="foreign(Alert.trip_id)==Trip.trip_id",
        viewonly=True,
    )
    stop = relationship(
        "Stop",
        back_populates="alerts",
        primaryjoin="foreign(Alert.stop_id)==Stop.stop_id",
        viewonly=True,
    )

    DATETIME_MAPPER = {
        "active_period_end": "end_datetime",
        "active_period_start": "start_datetime",
        "created_at": "created_at_datetime",
        "updated_at": "updated_at_datetime",
    }

    @reconstructor
    def init_on_load(self):
        """Loads active_period_end and active_period_start as datetime objects."""
        # pylint: disable=attribute-defined-outside-init
        for key, value in self.DATETIME_MAPPER.items():
            if getattr(self, key, None):
                setattr(self, value, isoparse(getattr(self, key)))

    def __repr__(self):
        return f"<Alert(id={self.alert_id})>"

    def get_realtime(
        self,
        session: Session,
        route_types: str,
        base_url: str = None,
        api_key: str = None,
    ) -> None:
        """Inserts alerts into realtime database.

        Args:
            engine (Engine): database engine
            route_types (str): route types to download, comma separated
            base_url (str, optional): base url for api. Defaults to environment variable MBTA_API_URL.
            api_key (str, optional): api key. Defaults to environment variable MBTA_API_Key.
        """

        url = (
            (base_url or os.environ.get("MBTA_API_URL"))
            + "/alerts?filter[route_type]="
            + route_types
            + "&filter[datetime]=NOW&include=routes,trips&api_key="
            + (api_key or os.environ.get("MBTA_API_Key"))
        )

        req = requests.get(url, timeout=500)

        if req.ok and req.json().get("data"):
            dataframe = df_unpack(
                pd.json_normalize(req.json()["data"], sep="_"), UNPACK_LIST
            )
        else:
            logging.error("Invalid response from MBTA Alerts: %s", req.text)
            dataframe = pd.DataFrame()

        dataframe.drop(
            columns=[col for col in dataframe.columns if col not in RENAME_DICT],
            axis=1,
            inplace=True,
        )
        dataframe.rename(columns=RENAME_DICT, inplace=True)
        dataframe.reset_index(inplace=True)
        for col in ["trip_id", "stop_id", "direction_id"]:
            if col not in dataframe.columns:
                dataframe[col] = np.nan

        dataframe["index"] = dataframe.index

        to_sql_excpetion(session, dataframe, self.__class__)

    # def as_dict(self):
    #     """Returns alert as dict."""
    #     return {
    #         "service_effect": self.service_effect,
    #         "alert_id": self.alert_id,
    #         "cause": self.cause,
    #         "timestamp": self.created_at_datetime.strftime("%m/%d/%Y %I:%M%p"),
    #         "age_days": (
    #             datetime.now(pytz.timezone("America/New_York"))
    #             - self.created_at_datetime
    #         ).days,
    #         "through": f"{self.start_datetime.strftime('%m/%d/%Y %I:%M%p')} - {self.end_datetime.strftime('%m/%d/%Y %I:%M%p') if hasattr(self, 'end_datetime') else 'Indefinite'}",
    #         "url": self.url,
    #         "description": self.description,
    #         "header": self.header,
    #         "short_header": self.short_header,
    #     }
