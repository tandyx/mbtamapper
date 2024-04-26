"""Module to hold decorators."""

import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable

from flask import abort, request
from sqlalchemy.orm import scoped_session


def removes_session(_func: Callable[..., Any]):
    """Decorator to remove a scroped session from a Feed object after function call. \
    This decorator also removes the session from the object if an exception is raised.

    Args:
        - `_func (function)`: Function to wrap. \n
    Returns:
        - `function`: Wrapped function.
    """

    def _removes_session(*args, **kwargs):
        """Wrapper for decorator. Removes session from Feed object after function call.

        Args:
            - `*args`: Positional arguments.
            - `**kwargs`: Keyword arguments. \n
        Returns:
            - `Any`: Result of function call.
        """
        res = None
        try:
            res = _func(*args, **kwargs)
        except Exception as err:  # pylint: disable=broad-except
            logging.error(
                "Error in %s: %s %s", _func.__name__, err, traceback.format_exc()
            )
        for arg in args:
            for attr_name in dir(arg):
                attr = getattr(arg, attr_name)
                if isinstance(attr, scoped_session):
                    attr.remove()
                    return res
        return res

    return _removes_session


def timeit(_func: Callable[..., Any], round_to: int = 3):
    """Decorator to time a function and log it.

    Args:
        - `_func (function)`: Function to wrap.
        - `round_to (int, optional)`: Number of decimal places to round to. Defaults to 3. \n
    Returns:
        - `function`: Wrapped function.
    """

    def _timeit(*args, **kwargs) -> Any:
        """Wrapper for decorator."""
        start = time.perf_counter()
        res = _func(*args, **kwargs)
        logging.info(
            "Ran %s in %f s",
            _func.__name__,
            round(time.perf_counter() - start, round_to),
        )
        return res

    return _timeit


def limit_content_length(max_length: int):
    """Decorator to limit the content length of a request.

    args:
        - `max_length (int)`: Maximum length of request. \n
    returns:
        - `function`: Wrapped function.
    """

    def decorator(f):
        """Wrapper for decorator."""

        @wraps(f)
        def wrapper(*args, **kwargs):
            """Wrapper for decorator."""
            # cl =
            if request.method == "GET":
                data = f(*args, **kwargs)
                if len(data) > max_length:
                    abort(413)
                return data
            cl = request.content_length
            if cl is not None and cl > max_length:
                abort(413)
            return f(*args, **kwargs)

        return wrapper

    return decorator


class classproperty(property):  # pylint: disable=invalid-name
    """Decorator to create a class property.

    Args:
        - `property (property)`: property to wrap. \n
    Returns:
        - `property`: Wrapped property."""

    def __get__(self, owner_self: object, owner_cls: object):
        """Gets the property.

        Args:
            - `owner_self (object)`: Owner object.
            - `owner_cls (object)`: Owner class. \n
        Returns:
            - `object`: Value of property.
        """
        return self.fget(owner_cls)
