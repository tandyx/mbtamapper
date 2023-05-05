import sqlite3
import polyline
from flask import Flask, render_template, jsonify, request
from shared_code.from_sql import GrabData
from poll_mbta_data import vehicles, routes, shapes, stops, predictions, alerts

app = Flask(__name__)
route_type = 1


@app.route("/")
def index():
    return render_template("index.html")


@app.route(f"/vehicles/{route_type}")
def get_vehicles():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabvehicles()
    alert_data = GrabData(route_type, conn).grabalerts()
    for index, row in data.iterrows():
        try:
            data.at[index, "alert"] = (
                alert_data[alert_data["trip_id"] == row["trip_id"]]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except ValueError:
            data.at[index, "alert"] = None

    data["alert"] = data["alert"].apply(lambda y: None if y == y and len(y) == 0 else y)
    # data["trip_short_name"] = data["trip_short_name"].fillna(data["trip_id"])
    # trip_alert = (
    #     alert_data.groupby("trip_id")["Value"]
    #     .apply(lambda x: dict(zip(range(len(x)), x)))
    #     .reset_index(name="DictValue")
    # )
    data.drop(columns=["polyline"], inplace=True)
    return jsonify(data.fillna("unknown").to_dict(orient="records"))


@app.route(f"/stops/{route_type}")
def get_stops():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabstops()
    alert_data = GrabData(route_type, conn).grabalerts()
    for index, row in data.iterrows():
        try:
            data.at[index, "alert"] = (
                alert_data[alert_data["stop_id"] == row["parent_station"]]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except ValueError:
            data.at[index, "alert"] = None
    data["alert"] = data["alert"].apply(lambda y: None if y == y and len(y) == 0 else y)
    return jsonify(data.fillna("unknown").to_dict(orient="records"))


@app.route(f"/shapes/{route_type}")
def get_shapes():
    conn = sqlite3.connect(f"mbta_data.db")
    data = GrabData(route_type, conn).grabshapes()
    alert_data = GrabData(route_type, conn).grabalerts()
    for index, row in data.iterrows():
        try:
            data.at[index, "alert"] = (
                alert_data[
                    (alert_data["route_id"] == row["route_id"])
                    & (alert_data["stop_id"].isna())
                    & (alert_data["trip_id"].isna())
                ]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except ValueError:
            data.at[index, "alert"] = None
    data["alert"] = data["alert"].apply(lambda y: None if y == y and len(y) == 0 else y)
    data["polyline"] = data["polyline"].apply(polyline.decode)
    data["route_name"] = data["route_name"].fillna(data["route_id"])
    data["description"].fillna("Bus Replacement")
    return jsonify(data.fillna("unknown").to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)
