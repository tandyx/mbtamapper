"""holds base class for all gtfs loader elements and initalizes sqlite foreign keys"""
import logging
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

# pylint disable=unused-argument
# pylint disable=too-few-public-methods

logging.getLogger().setLevel(logging.INFO)


class GTFSBase(DeclarativeBase):
    """Base class for all GTFS schedule elements"""

    __table_args__ = {"sqlite_autoincrement": False, "sqlite_with_rowid": False}


@event.listens_for(Engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """sets sqlite pragma for each connection"""
    # pylint: disable=unused-argument
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        for pragma in ["foreign_keys=ON", "auto_vacuum='1'", "shrink_memory"]:
            try:
                cursor.execute(f"PRAGMA {pragma}")
            except sqlite3.OperationalError:
                logging.warning("PRAGMA %s failed", pragma)
        cursor.close()


@event.listens_for(Engine, "close")
def on_close(dbapi_connection, connection_record):
    """sets sqlite pragma for each connection"""
    # pylint: disable=unused-argument
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA optimize")
        except sqlite3.OperationalError:
            logging.warning("PRAGMA optimize failed")
        cursor.close()
