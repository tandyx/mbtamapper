"""Flask app for MBTA GTFS data."""
from geojson import FeatureCollection

from sqlalchemy import select

from flask import Flask, render_template, jsonify, request
import atexit

from gtfs_loader import Feed

from gtfs_schedule import Shape, Stop
from gtfs_realtime import Vehicle
from shared_code.return_date import get_date

date = get_date(-4)

feed_list = [
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "0", date),
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "1", date),
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "2", date),
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "4", date),
]
stops: list[tuple[Stop]] = []
routes: list[tuple[Shape]] = []
for feed in feed_list:
    routes += feed.return_query(select(Shape))
    stops += feed.return_query(feed.queries.parent_stops_query)


app = Flask(__name__)


@app.route("/")
def index():
    """Returns index.html."""
    return render_template("index.html")


@app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    data: list[tuple[Vehicle]] = []
    for feed in feed_list:
        data += feed.query_vehicles()
    return jsonify([v[0].as_feature() for v in data])


@app.route("/stops")
def get_stops():
    """Returns stops as geojson."""
    return jsonify(FeatureCollection([s[0].as_feature() for s in stops]))


@app.route("/shapes")
def get_shapes():
    """Returns shapes as geojson."""

    return jsonify(
        FeatureCollection(
            sorted(
                [s[0].as_feature() for s in routes], key=lambda x: x["id"], reverse=True
            )
        )
    )


def exit_handler() -> None:
    """Closes all database sessions."""
    for feed in feed_list:
        feed.session.close()


if __name__ == "__main__":
    app.run(debug=True)
    atexit.register(exit_handler)
