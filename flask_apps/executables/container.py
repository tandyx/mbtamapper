"""This module contains the feed object that is used by the Flask app.""" ""
from gtfs_loader import Feed

FEED = Feed("https://cdn.mbta.com/MBTA_GTFS.zip")
# HOST = "0.0.0.0"
PORT = 500
HOST = "127.0.0.1"
