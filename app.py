import json
from gtfs_loader import Feed

from sqlalchemy import select

from flask import Flask, render_template, jsonify, Response
from gtfs_schedule import Shape, Stop
from gtfs_realtime import Vehicle
from geojson import dumps, FeatureCollection, dump

app = Flask(__name__)

feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "2")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    data: list[tuple[Vehicle]] = feed.session.execute(select(Vehicle))
    return jsonify(FeatureCollection([v[0].as_feature() for v in data]))


@app.route("/stops")
def get_stops():
    """Returns stops as geojson."""
    data: list[tuple[Stop]] = feed.session.execute(feed.queries.parent_stops_query)
    return jsonify(FeatureCollection([s[0].as_feature() for s in data]))


@app.route("/shapes")
def get_shapes():
    """Returns shapes as geojson."""
    data: list[tuple[Shape]] = feed.session.execute(select(Shape))
    return jsonify(
        FeatureCollection(
            sorted(
                [s[0].as_feature() for s in data], key=lambda x: x["id"], reverse=True
            )
        )
    )


if __name__ == "__main__":
    app.run(debug=True)
