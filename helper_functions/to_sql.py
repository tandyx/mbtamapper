"""Helper function to dump dataframe to sql."""
import logging
import time

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.exc import IllegalStateChangeError, IntegrityError
from sqlalchemy.orm import Session

from gtfs import GTFSBase

# pylint: disable=broad-except


def to_sql(
    session: Session,
    data: pd.DataFrame,
    orm: GTFSBase,
    purge: bool = False,
) -> None:
    """Helper function to dump dataframe to sql.

    Args:
        session (Session): sqlalchemy session
        data (pd.DataFrame): dataframe to dump
        orm (any): table to dump to
        purge (bool, optional): whether to purge table before dumping. Defaults to False.
    """

    if purge:
        session.execute(delete(orm))
        commited = False
        while not commited:
            try:
                session.commit()
                commited = True
            except IllegalStateChangeError:
                time.sleep(1)
                session.commit()

    try:
        res = data.to_sql(
            orm.__tablename__, session.connection().engine, None, "append", False
        )
    except IntegrityError:
        try:
            res = data.iloc[1:].to_sql(
                orm.__tablename__, session.connection().engine, None, "append", False
            )
        except Exception as error:
            logging.error("Failed to insert %s: %s", orm.__tablename__, error)
            return
    except Exception as error:
        logging.error("Failed to insert %s: %s", orm.__tablename__, error)
        return
    logging.info("Added %s rows to %s", res, orm.__tablename__)
