"""Helper functions for time conversions for gtfs loader"""

from datetime import datetime, timedelta

import pytz


def to_seconds(time: str) -> int:
    """Converts a string in HH:MM:SS format to seconds past midnight

    Args:
        - `time (str)`: A string in HH:MM:SS format
    Returns:
        - `int`: The number of seconds past midnight"""

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


def get_date(offset: int = 0, zone: str = "America/New_York") -> datetime:
    """Returns the current date in the given timezone

    Args:
        offset (int, optional): The number of hours to offset the date. Defaults to 0.
        zone (str, optional): The timezone to return the date in. Defaults to "America/New_York".
    Returns:
        datetime: The current date in the given timezone"""

    return datetime.now(pytz.timezone(zone)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(hours=offset)


def get_current_time(offset: int = 0, zone: str = "America/New_York") -> datetime:
    """Returns the current time in the given timezone

    Args:
        offset (int, optional): The number of hours to offset the time. Defaults to 0.
        zone (str, optional): The timezone to return the time in. Defaults to "America/New_York".
    Returns:
        datetime: The current time in the given timezone"""

    return datetime.now(pytz.timezone(zone)) + timedelta(hours=offset)
