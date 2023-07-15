"""Flask app for MBTA GTFS data."""
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
from geojson import FeatureCollection
from flask import Flask, render_template, jsonify
from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from gtfs_loader import Feed
from gtfs_loader.query import Query

# from gtfs_schedule import Shape, Stop
from gtfs_realtime import *
from shared_code.return_date import get_date

date = get_date(-4)

feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", date)
query = Query(["0", "1"])
session = scoped_session(feed.sessionmkr)

routes = ",".join(
    i[0].route_id for i in feed.session.execute(query.return_routes_query()).all()
)

app = Flask(__name__)


@app.route("/")
def index():
    """Returns index.html."""
    return render_template("index.html")


@app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    sess = session()
    Alert().get_realtime(sess, ",".join(query.route_types))
    Prediction().get_realtime(sess, routes)
    Vehicle().get_realtime(sess, ",".join(query.route_types))
    data: list[tuple[Vehicle]] = sess.execute(select(Vehicle)).all()
    return jsonify(FeatureCollection([v[0].as_feature() for v in data]))


@app.teardown_appcontext
def shutdown_session(exception=None) -> None:  # pylint: disable=unused-argument
    """Tears down database session."""

    session.remove()


# @app.route("/stops")
# def get_stops():
#     """Returns stops as geojson."""

#     data: list[tuple[Stop]] = session().execute(query.return_parent_stops()).all()
#     return jsonify(
#         FeatureCollection([s[0].as_feature(query.route_types) for s in data])
#     )


# @app.route("/shapes")
# def get_shapes():
#     """Returns shapes as geojson."""
#     routes: list[tuple[Shape]] = session().execute(query.return_shapes_query()).all()

#     return jsonify(
#         FeatureCollection(
#             sorted(
#                 [s[0].as_feature() for s in routes], key=lambda x: x["id"], reverse=True
#             )
#         )
#     )


if __name__ == "__main__":
    app.run(debug=True)
