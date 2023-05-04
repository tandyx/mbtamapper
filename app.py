import sqlite3
from flask import Flask, render_template, jsonify, request
from shared_code.from_sql import GrabData
from poll_mbta_data import vehicles, routes, shapes, stops, predictions, alerts

app = Flask(__name__)
route_type = 2


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/vehicles/")
def get_vehicles():
    conn = sqlite3.connect(f"mbta_data.db")
    vehicles.getvehicles(route_type, conn)
    data = (
        GrabData(route_type, conn).grabvehicles().fillna(0.0).to_dict(orient="records")
    )
    return jsonify(data)


@app.route("/stops/")
def get_stops():
    conn = sqlite3.connect(f"mbta_data.db")
    stops.getstops(route_type, conn)
    data = GrabData(route_type, conn).grabstops().fillna(0.0).to_dict(orient="records")
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
