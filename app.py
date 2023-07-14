"""Flask app for MBTA GTFS data."""
from geojson import FeatureCollection

from sqlalchemy import select

from flask import Flask, render_template, jsonify

from gtfs_loader import Feed
from gtfs_loader.flask_app import FlaskApp
from gtfs_schedule import Shape, Stop
from shared_code.return_date import get_date

feed_1 = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "0", get_date(-3))
feed_2 = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "1", get_date(-3))
flask_app = FlaskApp(Flask(__name__), [feed_1, feed_2])


@flask_app.app.route("/")
def index():
    """Returns index.html."""
    return render_template("index.html")


@flask_app.app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    data = flask_app.query_and_return_vehicles()
    return jsonify(FeatureCollection([v[0].as_feature() for v in data]))


@flask_app.app.route("/stops")
def get_stops():
    """Returns stops as geojson."""
    data: list[tuple[Stop]] = flask_app.return_data(Shape)
    return jsonify(FeatureCollection([s[0].as_feature() for s in data]))


@flask_app.app.route("/shapes")
def get_shapes():
    """Returns shapes as geojson."""
    data: list[tuple[Shape]] = flask_app.return_data(Shape)
    return jsonify(
        FeatureCollection(
            sorted(
                [s[0].as_feature() for s in data], key=lambda x: x["id"], reverse=True
            )
        )
    )


if __name__ == "__main__":
    flask_app.app.run(debug=True)
