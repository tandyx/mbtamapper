import sqlite3
import polyline
from flask import Flask, render_template, jsonify, request
from shared_code.from_sql import GrabData

app = Flask(__name__)
route_type = 2


@app.route("/")
def index():
    return render_template("index.html")


@app.route(f"/vehicles/{route_type}")
def get_vehicles():
    conn = sqlite3.connect("mbta_data.db")
    data = GrabData(route_type, conn).grabvehicles()
    alert_data = GrabData(route_type, conn).grabalerts()
    predictions = GrabData(route_type, conn).grabpredictions()
    for ind, row in data.iterrows():
        try:
            data.at[ind, "alert"] = (
                alert_data.loc[alert_data["trip_id"] == row["trip_id"], :]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except (ValueError, KeyError):
            data.at[ind, "alert"] = None
        try:
            data.at[ind, "predictions"] = predictions.loc[
                predictions["trip_id"] == row["trip_id"], :
            ].to_dict(orient="records")
        except (ValueError, KeyError):
            data.at[ind, "predictions"] = None

    data["alert"] = (
        data["alert"]
        .apply(lambda x: [x] if isinstance(x, dict) else x)
        .apply(lambda y: None if y == y and len(y) == 0 else y)
    )
    data["predictions"] = (
        data["predictions"]
        .apply(lambda x: [x] if isinstance(x, dict) else x)
        .apply(lambda y: None if y == y and len(y) == 0 else y)
    )

    # trip_alert = (
    #     alert_data.groupby("trip_id")["Value"]
    #     .apply(lambda x: dict(zip(range(len(x)), x)))
    #     .reset_index(name="DictValue")
    # )
    data["trip_short_name"] = data["trip_short_name"].fillna(data["trip_id"])
    data["stop_status"] = data["stop_status"].apply(
        lambda x: x.lower().replace("_", " ") if x == x else x
    )
    data.drop(columns=["polyline"], inplace=True)
    return jsonify(data.fillna("unknown").to_dict(orient="records"))


@app.route(f"/stops/{route_type}")
def get_stops():
    conn = sqlite3.connect("mbta_data.db")
    data = GrabData(route_type, conn).grabstops()
    alert_data = GrabData(route_type, conn).grabalerts()
    predictions = GrabData(route_type, conn).grabpredictions()
    for ind, row in data.iterrows():
        try:
            data.at[ind, "alert"] = (
                alert_data.loc[alert_data["stop_id"] == row["parent_station"], :]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except (ValueError, KeyError):
            data.at[ind, "alert"] = None
        try:
            data.at[ind, "predictions"] = (
                predictions.loc[predictions["stop_id"] == row["stop_id"], :]
                .drop_duplicates(subset="trip_id")
                .to_dict(orient="records")
            )
        except (ValueError, KeyError):
            data.at[ind, "predictions"] = None

    data["alert"] = (
        data["alert"]
        .apply(lambda x: [x] if isinstance(x, dict) else x)
        .apply(lambda y: None if y == y and len(y) == 0 else y)
    )
    data["predictions"] = (
        data["predictions"]
        .apply(lambda x: [x] if isinstance(x, dict) else x)
        .apply(lambda y: None if y == y and len(y) == 0 else y)
    )

    return jsonify(data.fillna("unknown").to_dict(orient="records"))


@app.route(f"/shapes/{route_type}")
def get_shapes():
    conn = sqlite3.connect("mbta_data.db")
    data = GrabData(route_type, conn).grabshapes()
    alert_data = GrabData(route_type, conn).grabalerts()
    for ind, row in data.iterrows():
        try:
            data.at[ind, "alert"] = (
                alert_data.loc[
                    (alert_data["route_id"] == row["route_id"])
                    & (alert_data["stop_id"].isna())
                    & (alert_data["trip_id"].isna()),
                    :,
                ]
                .drop_duplicates(subset="alert_id")
                .to_dict(orient="records")
            )
        except (ValueError, KeyError):
            data.at[ind, "alert"] = None
    # data["alert"] = data["alert"].apply(lambda y: None if y == y and len(y) == 0 else y)
    data["polyline"] = data["polyline"].apply(polyline.decode)
    data["route_name"] = data["route_name"].fillna(data["route_id"])
    data["description"].fillna("Bus Replacement")
    return jsonify(data.fillna("unknown").to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)
