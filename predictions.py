"""
Keolis AVL-ACSES Real-Time Interface
Azure Function to poll MBTA data at /predictions and create a daily trip stops table
2023-01-20
Keolis Digital Solutions - Service Delivery Team
"""
from datetime import datetime, timedelta
import logging
import os
import requests as rq
import pytz
import pandas as pd
import json_api_doc as jad


# pylint: disable=unused-argument
def main(vehicle_type=2) -> None:
    """Azure function, grabs MBTA trip stops data and upserts every 15 seconds"""
    logging.getLogger("azure").setLevel(logging.CRITICAL)
    # polls CR route data from MBTA
    rreq = rq.get(
        f"https://api-v3.mbta.com/routes?filter[type]=2&api_key={os.getenv('MBTA_API_Key')}",
        timeout=5,
    )
    logging.info("Received code %s from MBTA route", rreq.status_code)
    if rreq.ok:
        # processes route info
        routes = [route["id"] for route in rreq.json()["data"]]
        logging.info("Received %s routes from MBTA", len(routes))
        preq = rq.get(
            "https://api-v3.mbta.com/predictions?filter[route]="
            + ",".join(routes)
            + "&include=stop,trip,route,vehicle,schedule&api_key="
            + os.environ["MBTA_API_Key"],
            timeout=5,
        )
        logging.info("Received code %s from MBTA predictions", preq.status_code)

        if preq.ok:
            # Load in HASTUS code table

            jad_preds = jad.deserialize(preq.json())

        else:
            logging.error(
                "MBTA prediction response returned the following: %s", preq.text
            )  # prediction logging
    else:
        logging.error(
            "MBTA route response returned the following: %s", rreq.text
        )  # route logging


def vehicleexcept(vehicle):
    """gets vehicle ID when known, null when unknown"""
    try:
        return vehicle["id"]
    except TypeError:
        return vehicle


def tripexcept(trip):
    """gets trip name when available, null when n/a"""
    try:
        return trip["name"]
    except TypeError:
        return trip
