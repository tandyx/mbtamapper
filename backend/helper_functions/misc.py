"""miscellaneous helper functions that i'm too lazy to fit elsewhere"""

import subprocess

import gitinfo
import pandas as pd

from .types import GitInfo


def get_gitinfo() -> GitInfo:
    """Get git information about the current repository

    Returns:
        GitInfo: A dictionary containing git information
    """

    return gitinfo.get_git_info() | {
        "remote_url": subprocess.run(
            ["git", "remote", "get-url", "origin"], check=False, capture_output=True
        )
        .stdout.decode("utf-8")
        .strip()
    }


def df_unpack(
    dataframe: pd.DataFrame, *columns: str, prefix: bool = True, sep: str = "_"
) -> pd.DataFrame:
    """Unpacks a column of a dataframe that contains a list of dictionaries. \
        Returns a dataframe with the unpacked column and the original dataframe\
        with the packed column removed.

    Args:
        dataframe (pd.DataFrame): dataframe to unpack
        *columns (str): columns to unpack.
        prefix (bool, optional): whether to add prefix to unpacked columns. \
            Defaults to True. \n
        sep (str, optional): separator for prefix. Defaults to "_". \n
    Returns:
        pd.DataFrame: dataframe with unpacked columns
    """

    for col in columns:
        if col not in dataframe.columns:
            continue
        exploded = dataframe.explode(col)
        series = exploded[col].apply(pd.Series)
        if prefix:
            series = series.add_prefix(col + sep)
        dataframe = pd.concat([exploded.drop([col], axis=1), series], axis=1)
    return dataframe
