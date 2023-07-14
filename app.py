"""Flask app for MBTA GTFS data."""
from geojson import FeatureCollection

from sqlalchemy import select

from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import delete, insert
from sqlalchemy.exc import IntegrityError

from gtfs_loader import Feed
from gtfs_schedule import Shape, Stop, Route
from gtfs_realtime import Vehicle, Prediction, Alert

from poll_mbta_data import predictions, vehicles, alerts
from shared_code.return_date import get_date

feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "0", get_date(-3))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = feed.engine.url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

app2 = Flask(__name__)
feed2 = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "1", get_date(-3))
app2.config["SQLALCHEMY_DATABASE_URI"] = feed2.engine.url
app2.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db2 = SQLAlchemy(app2)


@app.route("/")
def index():
    """Returns index.html."""
    return render_template("index.html")


@app.route("/vehicles")
def get_vehicles():
    """Returns vehicles as geojson."""
    data = query_and_return_vehicles(db)
    return jsonify(FeatureCollection([v[0].as_feature() for v in data]))


@app.route("/stops")
def get_stops():
    """Returns stops as geojson."""
    data: list[tuple[Stop]] = db.session.execute(feed.queries.parent_stops_query).all()
    return jsonify(FeatureCollection([s[0].as_feature() for s in data]))


@app.route("/shapes")
def get_shapes():
    """Returns shapes as geojson."""
    data: list[tuple[Shape]] = db.session.execute(select(Shape)).all()
    return jsonify(
        FeatureCollection(
            sorted(
                [s[0].as_feature() for s in data], key=lambda x: x["id"], reverse=True
            )
        )
    )


def query_and_return_vehicles(db_obj: SQLAlchemy) -> list[tuple[Vehicle]]:
    """Downloads realtime data from the mbta api and returns active vehicles.
    Note that this method also deletes all realtime data from the database and replaces it

    Args:
        db_obj (SQLAlchemy): FlaskSQLAlchemy object
    Returns:
        list[tuple[Vehicle]]: list of vehicles"""

    active_routes = ",".join(
        item[0]
        for item in db_obj.session.execute(select(Route.route_id).distinct()).all()
    )

    orm_func_mapper = {
        Vehicle: vehicles.get_vehicles(feed.route_type),
        Alert: alerts.get_alerts(feed.route_type),
        Prediction: predictions.get_predictions(active_routes),
    }

    for orm, function in orm_func_mapper.items():
        try:
            db_obj.session.execute(delete(orm))
            db_obj.session.execute(
                insert(orm), function.to_dict(orient="records", index=True)
            )
        except IntegrityError:
            db_obj.session.rollback()
        db_obj.session.commit()

    return db_obj.session.execute(select(Vehicle)).all()


if __name__ == "__main__":
    app.run(debug=True)
