import sqlite3
from poll_mbta_data import alerts, routes, shapes, stops, vehicles, predictions


conn = sqlite3.connect("mbta_data.db")
for route_type in range(5):
    active_routes = routes.getroutes(route_type, conn)

    alerts.getalerts(route_type, conn)
    stops.getstops(route_type, conn)
    vehicles.getvehicles(route_type, conn)
    predictions.getpredictions(route_type, active_routes, conn)
    shapes.getshapes(route_type, active_routes, conn)
