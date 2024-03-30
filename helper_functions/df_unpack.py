"""Unpacks a column of a dataframe that contains a list of dictionaries."""

from typing import Any, Generator, Iterable

import pandas as pd


def df_unpack(
    dataframe: pd.DataFrame, columns: list[str], prefix: bool = True
) -> pd.DataFrame:
    """Unpacks a column of a dataframe that contains a list of dictionaries. \
        Returns a dataframe with the unpacked column and the original dataframe\
        with the packed column removed.

    Args:
        - `dataframe (pd.DataFrame)`: dataframe to unpack
        - `columns (list[str])`: columns to unpack.
        - `prefix (bool, optional)`: whether to add prefix to unpacked columns. \
            Defaults to True. \n
    Returns:
        - `pd.DataFrame`: dataframe with unpacked columns
    """

    for col in columns:
        if col not in dataframe.columns:
            continue
        exploded = dataframe.explode(col)
        series = exploded[col].apply(pd.Series)
        if prefix:
            series = series.add_prefix(col + "_")
        dataframe = pd.concat([exploded.drop([col], axis=1), series], axis=1)
    return dataframe


def list_unpack(list_to_unpack: Iterable[Any]) -> Generator[Any, None, None]:
    """Unpacks a list of dictionaries into a list of lists.

    Args:
        - `list_to_unpack (Iterable)`: iterable to unpack \n
    Returns:
        - `Generator[Any, None, None]`: generator of unpacked items
    """
    return (item for sublist in list_to_unpack for item in sublist)
