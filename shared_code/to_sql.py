import logging
from sqlalchemy import Engine
import pandas as pd
from gtfs_loader.gtfs_base import GTFSBase


def to_sql(
    engine: Engine, data: pd.DataFrame, orm: GTFSBase, index: bool = False
) -> None:
    """Helper function to dump dataframe to sql.

    Args:
        engine (Engine): sqlalchemy engine
        data (pd.DataFrame): dataframe to dump
        orm (any): table to dump to
        index (bool, optional): whether to include index in dump. Defaults to False.
    """
    res = data.to_sql(orm.__tablename__, engine, None, "append", index)
    logging.info("Added %s rows to %s", res, orm.__tablename__)
