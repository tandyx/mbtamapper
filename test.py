"""Test"""
import time
import logging
import schedule
from datetime import datetime

from gtfs_loader import Feed

from shared_code.return_date import get_date


def nightly_import(date: datetime = None) -> None:
    """Runs the nightly import.

    Args:
        date: The date to import. Defaults to today."""

    date = date or get_date()
    for route_type in ["0", "1", "2", "3", "4"]:
        logging.info("Loading route_type %s", route_type)
        feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", route_type, date)
        feed.import_gtfs()
        feed.purge_and_filter()
        feed.delete_old_databases()

    logging.info("Import Finished for %s", date.strftime("%Y-%m-%d"))


logging.getLogger().setLevel(logging.INFO)
schedule.every().day.at("00:00", tz="America/New_York").do(nightly_import, None)
while True:
    schedule.run_pending()
    time.sleep(60)  # wait one minute
