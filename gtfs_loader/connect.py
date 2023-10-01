"""Database connection and session management"""
import logging
import sqlite3
from sqlalchemy import event, pool
from sqlalchemy.engine import Engine


logging.getLogger().setLevel(logging.INFO)


# pylint: disable=unused-argument
@event.listens_for(Engine, "connect")
def on_connect(
    dbapi_connection: sqlite3.Connection, connection_record: pool.ConnectionPoolEntry
) -> None:
    """Sets sqlite pragma for each connection

    Args:
        dbapi_connection (sqlite3.Connection): connection to sqlite database
        connection_record (ConnectionRecord): connection record
    """

    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        for pragma in ["foreign_keys=ON", "auto_vacuum='1'", "shrink_memory"]:
            try:
                cursor.execute(f"PRAGMA {pragma}")
            except sqlite3.OperationalError:
                logging.warning("PRAGMA %s failed", pragma)
        cursor.close()


@event.listens_for(Engine, "close")
def on_close(
    dbapi_connection: sqlite3.Connection, connection_record: pool.ConnectionPoolEntry
) -> None:
    """Sets sqlite pragma on close

    Args:
        dbapi_connection (sqlite3.Connection): connection to sqlite database
        connection_record (ConnectionRecord): connection record
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA optimize")
        except sqlite3.OperationalError:
            logging.warning("PRAGMA optimize failed")
        cursor.close()
