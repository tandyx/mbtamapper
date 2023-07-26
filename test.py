"""Test"""
import os
import logging
import time
from dotenv import load_dotenv
import schedule
from sqlalchemy.exc import OperationalError

# from sqlalchemy import select

from gtfs_loader import Feed

load_dotenv()


def nightly_import(feed: Feed) -> None:
    """Runs the nightly import.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed.import_gtfs()
    feed.import_realtime()
    feed.purge_and_filter()
    # feed.import_realtime()


def geojson_exports(feed: Feed) -> None:
    """Exports geojsons.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed.import_realtime()
    geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
    for key in os.getenv("LIST_KEYS").split(","):
        try:
            feed.export_geojsons(key, geojson_path)
        except OperationalError:
            logging.warning("OperationalError: %s", key)


def update_realtime(feed: Feed) -> None:
    """Updates realtime data.

    Args:
        feed (Feed): GTFS feed (default: None)
    """
    feed.import_realtime()
    logging.info("Updated realtime data:, %s", feed)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    feed_obj = Feed(url="http://cdn.mbta.com/MBTA_GTFS.zip")
    # nightly_import(feed_obj)
    # geojson_exports(feed_obj)
    # update_realtime(feed_obj)
    schedule.every(5).seconds.do(update_realtime, feed_obj)
    schedule.every().day.at("03:30", tz="America/New_York").do(nightly_import, feed_obj)
    schedule.every().hour.at(":00", tz="America/New_York").do(geojson_exports, feed_obj)
    while True:
        schedule.run_pending()
        time.sleep(1)  # wait one minute
