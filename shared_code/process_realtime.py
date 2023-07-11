import logging
import requests
import pandas as pd

from df_unpack import df_unpack


def process_realtime(
    url: str, to_unpack: list[str], rename_dict: dict[str, str]
) -> pd.DataFrame:
    """Downloads realtime data from the mbta api."""

    req = requests.get(url, timeout=500)
    if req.ok:
        logging.info("Downloaded realtime data from %s", url)
    else:
        logging.error("Error downloading realtime data from %s", url)
        return
    dataframe = df_unpack(pd.json_normalize(req.json()["data"], sep="_"), to_unpack)

    # if "alert" in and

    dataframe.drop(
        columns=[col for col in dataframe.columns if col not in rename_dict.keys()],
        axis=1,
        inplace=True,
    )
    dataframe.rename(columns=rename_dict, inplace=True)

    return dataframe
