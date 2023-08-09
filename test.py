"""Test"""
import os
import logging
from dotenv import load_dotenv
from flask_apps import FEED
from gtfs_loader import FeedLoader
from helper_functions import instantiate_logger

load_dotenv()


if __name__ == "__main__":
    instantiate_logger(logging.getLogger())
    fead_loader = FeedLoader(FEED)
    # fead_loader.nightly_import()
    # fead_loader.geojson_exports()
    if not os.path.exists(fead_loader.feed.db_path):
        fead_loader.nightly_import()
        fead_loader.geojson_exports()
    fead_loader.scheduler()
