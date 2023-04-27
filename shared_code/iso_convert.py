import pandas as pd


def iso_convert(dataframe: pd.DataFrame, col_list: list):
    """pass in a list of coliumns to convert to iso format"""
    for col in col_list:
        dataframe[col] = pd.to_datetime(dataframe[col])
        try:
            dataframe[col] = (
                dataframe[col].dt.tz_localize("America/New_York").dt.tz_convert("UTC")
            )
        except TypeError:
            dataframe[col] = dataframe[col].dt.tz_convert("UTC")
        dataframe[col] = dataframe[col].map(lambda x: x.isoformat())
