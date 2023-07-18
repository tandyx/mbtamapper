"""Flask app for MBTA GTFS data."""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import os
from geojson import FeatureCollection

from flask import Flask, render_template, jsonify
from sqlalchemy import select
from sqlalchemy.orm import scoped_session
from gtfs_loader.query import Query
from gtfs_loader.feed import Feed
from gtfs_realtime import *
from shared_code.gtfs_helper_time_functions import get_date


feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", get_date(-1))


class FlaskApp:
    """Flask app for MBTA GTFS data.

    Attributes:
        app (Flask): Flask app
        feed_obj (Feed): GTFS feed
        key (str): key for route types
    """

    def __init__(self, app: Flask, feed_obj: Feed, key: str = None):
        self.app = app
        self.feed = feed
        self.key = key or "ALL_ROUTES"
        self.route_types = os.environ.get(key)
        self.query = Query(self.route_types.split(","))
        self.session = scoped_session(self.feed.sessionmkr)
        self.routes = self._get_routes()
        self._setup_routes()

    def __repr__(self) -> str:
        return f"<FlaskApp(key={self.key}, feed={self.feed})>"

    def _get_routes(self) -> str:
        """Returns a comma-separated string of route IDs."""
        return ",".join(
            i[0].route_id
            for i in self.session.execute(self.query.return_routes_query()).all()
        )

    def _setup_routes(self):
        """Sets up the app routes."""
        self.app.route("/")(self.render_map)
        self.app.route("/value")(self.get_value)
        self.app.route("/vehicles")(self.get_vehicles)
        self.app.teardown_appcontext(self.shutdown_session)

    def render_map(self):
        """Returns index.html."""
        return render_template("map.html")

    def render_index(self):
        """Returns index.html."""
        return render_template("index.html")

    def get_value(self):
        """Returns value of KEY."""
        return self.key

    def get_vehicles(self):
        """Returns vehicles as geojson."""
        sess = self.session()
        Alert().get_realtime(sess, self.route_types)
        Prediction().get_realtime(sess, self.routes)
        Vehicle().get_realtime(sess, self.route_types)
        data: list[tuple[Vehicle]] = sess.execute(select(Vehicle)).all()
        geojson_features = [v[0].as_feature() for v in data]
        return jsonify(FeatureCollection(geojson_features))

    # pylint: disable=unused-argument
    def shutdown_session(self, exception=None) -> None:
        """Tears down database session."""
        self.session.remove()

    def run(self, **options) -> None:
        """Runs the app."""
        self.app.run(**options)
