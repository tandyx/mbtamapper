"""Test"""
import os
import logging

from gtfs_loader.feed import Feed
from gtfs_loader.query import Query
from gtfs_realtime import Alert, Prediction, Vehicle

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
    # feed.import_gtfs()
    # query = Query(["0", "1"])
    # routes = ",".join(
    #     i[0].route_id for i in feed.session.execute(query.return_routes_query()).all()
    # )
    # Prediction().get_realtime(feed.engine, routes, MBTA_API_URL, MBTA_API_KEY)
    # Vehicle().get_realtime(
    #     feed.engine, ",".join(query.route_types), MBTA_API_URL, MBTA_API_KEY
    # )
    geojson_path = os.path.join(os.getcwd(), "static", "geojsons")
    for query_obj in [
        Query(["0", "1", "4"]),
        Query(["2"]),
        Query(["3"]),
        Query(["4"]),
        Query(["0", "1", "2", "3", "4"]),
    ]:
        Alert().get_realtime(
            feed.engine, ",".join(query_obj.route_types), MBTA_API_URL, MBTA_API_KEY
        )
        feed.export_geojsons(query_obj, geojson_path)


if __name__ == "__main__":
    nightly_import()
    # app.run(debug=True, host="


# logging.getLogger().setLevel(logging.INFO)
# schedule.every().day.at("00:00", tz="America/New_York").do(nightly_import, None)
# while True:
#     schedule.run_pending()
#     time.sleep(60)  # wait one minute
