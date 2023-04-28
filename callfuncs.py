import sqlite3
from poll_mbta_data import alerts, routes, shapes, stops, vehicles


conn = sqlite3.connect("mbta_data.db")
for route_type in range(5):
    routes.getroutes(route_type, conn)
    alerts.getalerts(route_type, conn)
    stops.getstops()
    vehicles.getvehicles()

    shapes.getshapes()
