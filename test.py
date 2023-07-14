"""Test"""
import logging
from gtfs_loader import Feed

from shared_code.return_date import get_date


logging.getLogger().setLevel(logging.INFO)

date = get_date()
for route_type in ["0", "1", "2", "3", "4"]:
    logging.info("Loading route_type %s", route_type)
    feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", route_type, date)
    feed.import_gtfs()
    feed.purge_and_filter()
    feed.delete_old_databases(date)
