"""Test"""
import os
import logging
import time
from dotenv import load_dotenv
import schedule

# from sqlalchemy import select

from gtfs_loader import Feed
from helper_functions import get_date, get_current_time

load_dotenv()


def nightly_import(feed: Feed = None) -> None:
    """Runs the nightly import.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date())
    feed.import_gtfs()
    feed.purge_and_filter()
    # feed.import_realtime()
    feed.delete_old_databases()


def geojson_exports(feed: Feed = None) -> None:
    """Exports geojsons.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date())
    feed.import_realtime()
    geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
    for key in os.getenv("LIST_KEYS").split(","):
        feed.export_geojsons(key, geojson_path)


def update_realtime(feed: Feed = None) -> None:
    """Updates realtime data.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_current_time(-1))
    feed.import_realtime()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed = Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date())
    # nightly_import(feed)
    # geojson_exports(feed)
    # update_realtime(feed)
    schedule.every(5).seconds.do(update_realtime)
    schedule.every().day.at("00:00", tz="America/New_York").do(nightly_import, None)
    schedule.every(60).minutes.at(":00", tz="America/New_York").do(
        geojson_exports, None
    )
    while True:
        schedule.run_pending()
        time.sleep(1)  # wait one minute
