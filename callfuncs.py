import sqlite3
import time
from poll_mbta_data import alerts, routes, shapes, stops, vehicles, predictions


conn = sqlite3.connect("mbta_data.db")
start_time = time.time()

for route_type in [0, 1, 2, 3, 4]:
    active_routes = routes.getroutes(route_type, conn)

    alerts.getalerts(route_type, conn)
    stops.getstops(route_type, conn)
    shapes.getshapes(route_type, active_routes, conn)
    vehicles.getvehicles(route_type, conn)
    if route_type != 3:
        predictions.getpredictions(route_type, active_routes, conn)
    shapes.getshapes(route_type, active_routes, conn)
print(f"Time elapsed: {time.time() - start_time:.2f} seconds")
