import logging
import requests as rq
import pandas as pd


def query_helper(url) -> pd.DataFrame:
    """Helper function to query the mbta api.

    Args:
        url (str): url to query
    Returns:
        pd.DataFrame: dataframe of query results"""

    req = rq.get(url, timeout=500)

    if req.ok and req.json().get("data"):
        return pd.json_normalize(req.json()["data"], sep="_")
    else:
        logging.error("Failed to query vehicles: %s", req.text)
        return pd.DataFrame()
