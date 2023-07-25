"""test"""
import requests as rq
import pandas as pd
from google.transit.gtfs_realtime_pb2 import FeedMessage
from protobuf_to_dict import protobuf_to_dict

from helper_functions import df_unpack


def get_alerts() -> None:
    """main"""
    feed = FeedMessage()
    response = rq.get("https://cdn.mbta.com/realtime/Alerts.pb", timeout=10)
    feed.ParseFromString(response.content)
    alert_dict = protobuf_to_dict(feed)["entity"]
    alert_df = df_unpack(
        pd.json_normalize(alert_dict, sep="_"),
        [
            "alert_informed_entity",
            "alert_informed_entity_trip",
            "alert_active_period",
            "alert_header_text_translation",
            "alert_description_text_translation",
            "alert_url_translation",
        ],
    )
    print()


def get_vehicles() -> None:
    """main"""
    feed = FeedMessage()
    response = rq.get("https://cdn.mbta.com/realtime/VehiclePositions.pb", timeout=10)
    feed.ParseFromString(response.content)
    print()


def get_tripupdates() -> None:
    """main"""
    feed = FeedMessage()
    response = rq.get("https://cdn.mbta.com/realtime/TripUpdates.pb", timeout=10)
    feed.ParseFromString(response.content)
    print()


if __name__ == "__main__":
    get_alerts()
