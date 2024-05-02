"""Helper functions for time conversions for gtfs loader"""

from datetime import datetime, timedelta

import pytz


def to_seconds(time: str) -> int:
    """Converts a string in HH:MM:SS format to seconds past midnight

    Args:
        - `time (str)`: A string in HH:MM:SS format
    Returns:
        - `int`: The number of seconds past midnight
    """

    hours, minutes, seconds = time.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def get_date(offset: int = 0, zone: str = "America/New_York") -> datetime:
    """Returns the current date in the given timezone

    Args:
        - `offset (int, optional)`: The number of days to offset. Defaults to 0.
        - `zone (str, optional)`: The timezone. Defaults to "America/New_York".\n
    Returns:
        - `datetime`: The current date in the given timezone
    """

    return datetime.now(pytz.timezone(zone)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=offset)


def get_current_time(offset: int = 0, zone: str = "America/New_York") -> datetime:
    """Returns the current time in the given timezone

    Args:
        - `offset (int, optional)`: The number of hours to offset the time. Defaults to 0.
        - `zone (str, optional)`: The timezone. Defaults to "America/New_York".\n
    Returns:
        - `datetime`: The current time in the given timezone
    """

    return datetime.now(pytz.timezone(zone)) + timedelta(hours=offset)
