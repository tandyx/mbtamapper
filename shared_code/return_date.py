from datetime import datetime, timedelta
import pytz


def get_date(offset: int = 0, zone: str = "America/New_York") -> datetime:
    """Returns the current date in the given timezone

    Args:
        offset (int, optional): The number of hours to offset the date. Defaults to 0.
        zone (str, optional): The timezone to return the date in. Defaults to "America/New_York".
    Returns:
        datetime: The current date in the given timezone"""

    return datetime.now(pytz.timezone(zone)) + timedelta(hours=offset)
