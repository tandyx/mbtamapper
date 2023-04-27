import logging
import pandas as pd


def calc_delay(dataframe, scheduled, predicted, unit="minutes"):
    """Calculates delay across a column of scheduled and predicted times,
    returns a column of delay data in the specified unit
    (default: unit="minutes", specify unit="seconds" for seconds)"""
    try:
        column = (
            pd.to_datetime(dataframe[scheduled], utc=True)
            - pd.to_datetime(dataframe[predicted], utc=True)
        ).dt.total_seconds()

        if unit == "seconds":
            column = column.div(1)
        elif unit == "minutes":
            column = column.div(60)
        elif unit == "hours":
            column = column.div(60 * 60)
        elif unit == "days":
            column = column.div(60 * 60 * 24)
        elif unit == "weeks":
            column = column.div(60 * 60 * 24 * 7)
        elif unit == "years":
            column = column.div(60 * 60 * 24 * 7 * 52)
        else:
            logging.error("invalid unit")
        return column
    except KeyError:
        return None
