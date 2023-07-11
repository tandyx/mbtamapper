import logging
from gtfs_loader import Feed


logging.getLogger().setLevel(logging.INFO)
feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "2")
# feed.import_gtfs()
# feed.purge_and_filter()
feed.download_realtime_data()
print()
