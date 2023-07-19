"""Custom class for grenerating blueprint for flask app"""
import os
from geojson import FeatureCollection
from flask import Blueprint, render_template, jsonify
from sqlalchemy import select
from sqlalchemy.orm import scoped_session
from gtfs_loader import Feed, Query
from gtfs_realtime import Alert, Prediction, Vehicle


class BluePrintApp:
    """Flask app for MBTA GTFS data. Use name as key for route types.

    Attributes:
        app (Flask): Flask app
        feed_obj (Feed): GTFS feed
    """

    def __init__(self, blueprint: Blueprint, feed: Feed):
        self.blueprint = blueprint
        self.feed = feed
        self.route_types = os.environ.get(blueprint.name)
        self.query = Query(self.route_types.split(","))
        self.session = scoped_session(self.feed.sessionmkr)
        self.routes = self._get_routes()
        self._setup_routes()

    def __repr__(self) -> str:
        return f"<BluePrintApp(blueprint={self.blueprint}, feed={self.feed})>"

    def _setup_routes(self):
        """Sets up the app routes."""
        self.blueprint.route("/")(self.render_map)
        self.blueprint.route("/value")(self.get_value)
        self.blueprint.route("/vehicles")(self.get_vehicles)

    def _get_routes(self) -> str:
        """Returns a comma-separated string of route IDs."""
        return ",".join(
            i[0].route_id
            for i in self.session.execute(self.query.return_routes_query()).all()
        )

    def render_map(self):
        """Returns index.html."""
        return render_template("map.html")

    def render_index(self):
        """Returns index.html."""
        return render_template("index.html")

    def get_value(self):
        """Returns value of KEY."""
        return self.blueprint.name

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
        self.run(**options)
