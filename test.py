import logging
from gtfs_loader import Feed


logging.getLogger().setLevel(logging.INFO)


for route_type in ["0", "1", "2", "3", "4"]:
    logging.info("Loading route_type %s", route_type)
    feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", route_type)
    feed.import_gtfs()
    feed.purge_and_filter()
