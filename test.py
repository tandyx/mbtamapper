"""Test"""
import os
import logging
import time
from dotenv import load_dotenv
import schedule

# from sqlalchemy import select

from gtfs_loader import Feed
from helper_functions import get_date

load_dotenv()


def nightly_import(feed: Feed = None) -> None:
    """Runs the nightly import.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date())
    # feed.import_gtfs()
    # feed.purge_and_filter()
    feed.import_realtime()
    feed.delete_old_databases()


def geojson_exports(feed: Feed = None) -> None:
    """Exports geojsons.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date())
    geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
    for key in os.getenv("LIST_KEYS").split(","):
        feed.export_geojsons(key, geojson_path)


def update_realtime(feed: Feed = None) -> None:
    """Updates realtime data.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed = feed or Feed(url=os.environ.get("GTFS_ZIP_LINK"), date=get_date(0))
    feed.import_realtime()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    # nightly_import(Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date()))
    geojson_exports(Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date()))
    update_realtime(Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(0)))
    schedule.every(15).seconds.do(update_realtime, None)
    schedule.every().day.at("00:00", tz="America/New_York").do(nightly_import, None)
    schedule.every(60).minutes.at(":00", tz="America/New_York").do(
        geojson_exports, None
    )
    while True:
        schedule.run_pending()
        time.sleep(60)  # wait one minute
