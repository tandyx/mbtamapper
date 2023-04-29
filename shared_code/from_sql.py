from dataclasses import dataclass
import pandas as pd
import sqlite3


@dataclass
class GrabData:
    """grabs data from sqlite database and returns pandas dataframe"""

    route_type: int = 2
    conn: sqlite3.Connection = sqlite3.connect(f"mbta_data.db")

    def __post_init__(self):
        self.offset = 0 if self.route_type == 1 else 1

    def grabvehicles(self):
        if self.route_type in [0, 1]:
            vehicles = read_query(
                f"""SELECT * FROM (
                    (SELECT * FROM vehicles_{self.route_type}
                    UNION SELECT * FROM vehicles_{self.offset}) as vehicles
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type}
                    UNION SELECT route_id, route_name, description from routes_{self.offset}) as routes 
                    ON vehicles.route_id = routes.route_id) as a
					LEFT JOIN (SELECT * FROM shapes_{self.route_type} UNION SELECT * FROM shapes_{self.offset}) as shapes on shapes.route_id = a.route_id
					GROUP BY vehicle_id;""",
                self.conn,
            )
        else:
            vehicles = read_query(
                f"""SELECT * FROM (
                    SELECT * FROM vehicles_{self.route_type} as vehicles 
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type}) as routes 
                    ON vehicles.route_id = routes.route_id) as a
					LEFT JOIN shapes_{self.route_type} on shapes_{self.route_type} .route_id = a.route_id
					GROUP BY vehicle_id;""",
                self.conn,
            )
        return vehicles

    def grabstops(self):
        if self.route_type in [0, 1]:
            stops = read_query(
                f"""SELECT * FROM (
                    SELECT * FROM stops_{self.route_type} UNION SELECT * FROM stops_{self.offset}) as a 
                    GROUP BY a.parent_station, a.line_serviced 
                    ORDER BY a.parent_station, a.line_serviced""",
                self.conn,
            )
            return stops
        else:
            stops = read_query(
                f"""SELECT * FROM stops_0 
                                   GROUP BY parent_station, line_serviced 
                                   ORDER BY parent_station, line_serviced;""",
                self.conn,
            )
        return stops

    def grabshapes(self):
        if self.route_type in [0, 1]:
            shapes = read_query(
                f"""SELECT * FROM (
                    SELECT * FROM (
                    (SELECT * FROM shapes_{self.route_type}
                    UNION SELECT * FROM shapes_{self.offset})as shapes
                    LEFT JOIN 
                    (SELECT route_id, route_name, description from routes_{self.route_type} 
                    UNION SELECT route_id, route_name, description from routes_{self.offset}) as routes 
                    ON shapes.route_id = routes.route_id));""",
                self.conn,
            )
        else:
            shapes = read_query(
                f"""SELECT * FROM (SELECT * FROM shapes_{self.route_type} as shapes
                    LEFT JOIN 
                    (SELECT route_id, route_name, description from routes_{self.route_type}) as routes 
                    ON shapes.route_id = routes.route_id) 
                    ORDER BY shape_id desc;""",
                self.conn,
            )
        return shapes

    def grabpredictions(self):
        if self.route_type in [0, 1]:
            predictions = read_query(
                f"""SELECT * FROM (
                    (SELECT * FROM predictions_{self.route_type}  
                    UNION SELECT * FROM predictions_{self.offset})as prd 
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type} 
                    UNION SELECT route_id, route_name, description from routes_{self.offset}) as routes 
                    ON prd.route_id = routes.route_id);""",
                self.conn,
            )
        else:
            predictions = read_query(
                f"""SELECT * FROM (
                    SELECT * FROM predictions_{self.route_type}  as prd 
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type}) as routes 
                    ON prd.route_id = routes.route_id);""",
                self.conn,
            )
        return predictions

    def grabalerts(self):
        if self.route_type in [0, 1]:
            alerts = read_query(
                f"""SELECT * FROM (SELECT * FROM (
                    (SELECT * FROM alerts_{self.route_type} UNION SELECT * FROM alerts_{self.offset})  as alerts 
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type} 
                    UNION SELECT route_id, route_name, description from routes_{self.offset}) as routes 
                    ON alerts.route_id == routes.route_id));""",
                self.conn,
            )
        else:
            alerts = read_query(
                f"""SELECT * FROM (
                    SELECT * FROM alerts_{self.route_type}  as alerts 
                    LEFT JOIN (
                    SELECT route_id, route_name, description from routes_{self.route_type}) as routes 
                    ON alerts.route_id == routes.route_id);""",
                self.conn,
            )
        return alerts


def read_query(query, conn=sqlite3.connect(f"mbta_data.db")):
    """Read query from sqlite database"""
    try:
        result = pd.read_sql_query(query, conn)
    except Exception:
        result = pd.DataFrame()
    return result
