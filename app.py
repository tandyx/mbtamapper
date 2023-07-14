"""Flask app for MBTA GTFS data."""
from geojson import FeatureCollection

from sqlalchemy import select

from flask import Flask, render_template, jsonify, request

from sqlalchemy.orm import scoped_session, sessionmaker

from gtfs_loader import Feed

from gtfs_schedule import Shape, Stop
from gtfs_realtime import Vehicle
from shared_code.return_date import get_date

date = get_date(-4)

feed_list = [
    # Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "0", date),
    # Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "1", date),
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "2", date),
    Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "4", date),
]

session_dict = {
    feed: scoped_session(sessionmaker(bind=feed.engine, expire_on_commit=False))
    for feed in feed_list
}

app = Flask(__name__)


@app.route("/")
def index():
    """Returns index.html."""
    return render_template("index.html")


@app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    data: list[tuple[Vehicle]] = []
    for feed, session in session_dict.items():
        data += feed.query_vehicles(session())
    return jsonify(FeatureCollection([v[0].as_feature() for v in data]))


@app.route("/stops")
def get_stops():
    """Returns stops as geojson."""

    data: list[tuple[Stop]] = []
    for session in session_dict.values():
        data += session().execute(select(Stop).where(Stop.location_type == "1")).all()
    return jsonify(FeatureCollection([s[0].as_feature() for s in data]))


@app.route("/shapes")
def get_shapes():
    """Returns shapes as geojson."""
    routes: list[tuple[Shape]] = []
    for session in session_dict.values():
        routes += session().execute(select(Shape)).all()

    return jsonify(
        FeatureCollection(
            sorted(
                [s[0].as_feature() for s in routes], key=lambda x: x["id"], reverse=True
            )
        )
    )


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Tears down database session."""
    for session in session_dict.values():
        session.remove()


if __name__ == "__main__":
    app.run(debug=True)
