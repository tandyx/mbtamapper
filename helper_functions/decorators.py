"""Module to hold decorators."""
import logging
import time
import traceback
from typing import Any, Callable

from sqlalchemy.orm import scoped_session


def removes_session(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to remove a scroped session from a Feed object after function call. \
    This decorator also removes the session from the object if an exception is raised.

    Args:
        func (function): Function to wrap.
    Returns:
        function: Wrapped function.
    """

    def _removes_session(*args, **kwargs) -> Any:
        """Wrapper for decorator. Removes session from Feed object after function call."""
        try:
            res = func(*args, **kwargs)
        except Exception as err:  # pylint: disable=broad-except
            logging.error(
                "Error in %s: %s %s", func.__name__, err, traceback.format_exc()
            )
            res = None
        for arg in args:
            for attr_name in dir(arg):
                attr = getattr(arg, attr_name)
                if isinstance(attr, scoped_session):
                    attr.remove()
        return res

    return _removes_session


def timeit(func: Callable[..., Any], round_to: int = 3) -> Callable[..., Any]:
    """Decorator to time a function and log it.

    Args:
        func (function): Function to wrap.
        round_to (int, optional): Number of decimal places to round to. Defaults to 3.
    Returns:
        function: Wrapped function.
    """

    def _timeit(*args, **kwargs) -> Any:
        """Wrapper for decorator."""
        start = time.perf_counter()
        res = func(*args, **kwargs)
        logging.info(
            "Ran %s in %f s",
            func.__name__,
            round(time.perf_counter() - start, round_to),
        )
        return res

    return _timeit


class classproperty(property):  # pylint: disable=invalid-name
    """Decorator to create a class property.

    Args:
        property (property): property to wrap.
    Returns:
        property: Wrapped property."""

    def __get__(self, owner_self: object, owner_cls: object):
        return self.fget(owner_cls)
