"""Defines helper functions for string operations."""

import json
from typing import Any


def shorten(string: str, length: int = 20, suffix: str = "...") -> str:
    """Shortens a string to a certain length.

    Args:
        - `string (str)`: String to shorten.
        - `length (int, optional)`: Length to shorten to. Defaults to 20.
        - `suffix (str, optional)`: Suffix to add to the end of the string. Defaults to `"..."`. \n
    Returns:
        - `str`: Shortened string.
    """
    return (string[:length] + suffix) if len(string) > length else string


def is_json_searializable(obj: Any) -> bool:
    """Checks if an object is JSON serializable.

    Args:
        - `obj (Any)`: Object to check. \n
    Returns:
        - `bool`: Whether the object is JSON serializable.
    """
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False
