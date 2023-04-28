import pandas as pd
import sqlite3


def read_query(query, conn=sqlite3.connect(f"mbta_data.db")):
    """Read query from sqlite database"""
    try:
        query = pd.read_sql_query(query, conn)
    except Exception:
        query = pd.DataFrame()
    return query
