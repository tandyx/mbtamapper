import sqlite3
import polyline
from flask import Flask, render_template, jsonify, request
from shared_code.from_sql import GrabData
from poll_mbta_data import vehicles, routes, shapes, stops, predictions, alerts

app = Flask(__name__)
route_type = 2


@app.route("/")
def index():
    return render_template("index.html")


@app.route(f"/vehicles/{route_type}")
def get_vehicles():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabvehicles().to_dict(orient="records")
    return jsonify(data)


@app.route(f"/stops/{route_type}")
def get_stops():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabstops().to_dict(orient="records")
    return jsonify(data)


@app.route(f"/shapes/{route_type}")
def get_shapes():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabshapes()
    data["polyline"] = data["polyline"].apply(polyline.decode)
    data = data.to_dict(orient="records")
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
