"""Test"""
import os
import logging

from gtfs_loader.feed import Feed
from gtfs_realtime import Alert
from shared_code.return_date import get_date

MBTA_API_KEY = "98945a313953423b80d585ecb7582b1a"
MBTA_API_URL = "https://api-v3.mbta.com"


print()


def nightly_import() -> None:
    """Runs the nightly import.

    Args:
        date: The date to import. Defaults to today."""

    logging.getLogger().setLevel(logging.INFO)
    feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date())
    feed.import_gtfs()
    geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
    for key in ["SUBWAY", "RAPID_TRANSIT", "COMMUTER_RAIL", "BUS", "FERRY"]:
        Alert().get_realtime(feed.session, os.environ.get(key))
        feed.export_geojsons(key, geojson_path)


if __name__ == "__main__":
    nightly_import()
    # app.run(debug=True, host="


# logging.getLogger().setLevel(logging.INFO)
# schedule.every().day.at("00:00", tz="America/New_York").do(nightly_import, None)
# while True:
#     schedule.run_pending()
#     time.sleep(60)  # wait one minute
