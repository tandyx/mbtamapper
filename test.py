from shared_code.from_sql import GrabData
import sqlite3

route_type = 2
conn = sqlite3.connect(f"mbta_data.db")
print("hi")
GrabData(route_type, conn).grabvehicles()
