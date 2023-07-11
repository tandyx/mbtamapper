"""Helper functions for time conversions for gtfs loader"""
from datetime import datetime, timedelta
import pytz


def to_seconds(time: str) -> int:
    """Converts a string in HH:MM:SS format to seconds past midnight

    Args:
        time (str): A string in HH:MM:SS format
    Returns:
        int: The number of seconds past midnight"""

    hours, minutes, seconds = time.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def seconds_to_iso(date: datetime, seconds: int, zone: str = "America/New_York") -> str:
    """Converts a date and seconds to an iso string

    Args:
        date (datetime): The date of the service
        seconds (int): The seconds past midnight
        zone (str, optional): The timezone of the service. Defaults to "America/New_York".
    Returns:
        str: An iso string"""

    date_time = pytz.timezone(zone).localize(date + timedelta(seconds=seconds))
    return date_time.astimezone(pytz.utc).isoformat()


def to_transitvision_iso(seconds: int) -> str:
    """Converts seconds past midnight to an iso string for transitvision

    Args:
        seconds (int): The seconds past midnight
    Returns:
        str: An iso string"""

    date_time = datetime(1900, 1, 1, 0, 0, 0) + timedelta(seconds=seconds)
    return date_time.isoformat()
