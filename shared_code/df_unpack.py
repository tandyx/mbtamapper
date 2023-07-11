import pandas as pd


def df_unpack(
    dataframe: pd.DataFrame, columns: list[str] = None, prefix: bool = True
) -> pd.DataFrame:
    """Unpacks a column of a dataframe that contains a list of dictionaries.
    Returns a dataframe with the unpacked column and the original dataframe
    with the packed column removed.

    Args:
        dataframe (pd.DataFrame): dataframe to unpack
        columns (list[str], optional): columns to unpack. Defaults to None.
        prefix (bool, optional): whether to add prefix to unpacked columns. Defaults to True.
    Returns:
        pd.DataFrame: dataframe with unpacked columns
    """

    columns = columns or []

    for col in columns:
        if col not in dataframe.columns:
            continue
        exploded = dataframe.explode(col)
        series = exploded[col].apply(pd.Series)
        if prefix:
            series = series.add_prefix(col + "_")
        dataframe = pd.concat([exploded.drop([col], axis=1), series], axis=1)

    return dataframe
