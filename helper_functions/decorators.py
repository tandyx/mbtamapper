"""Module to hold decorators."""
import logging
import time
import traceback

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import scoped_session


def removes_session(func):
    """Decorator to remove a scroped session from a Feed object after function call.
    This decorator also removes the session from the object if an exception is raised.

    Args:
        func (function): Function to wrap.
    """

    def wrapper(*args, **kwargs):
        """Wrapper for decorator. Removes session from Feed object after function call."""
        try:
            res = func(*args, **kwargs)
        except (OperationalError, IntegrityError) as err:
            logging.error("OperationalError: %s", err)
            logging.error(traceback.format_exc())
            res = None
        for arg in args:
            for attr in dir(arg):
                if isinstance(getattr(arg, attr), scoped_session):
                    getattr(arg, attr).remove()
        return res

    return wrapper


def timeit(func, round_to: int = 3):
    """Decorator to time a function and log it."""

    def wrapper(*args, **kwargs):
        """Wrapper for decorator."""
        start = time.perf_counter()
        res = func(*args, **kwargs)
        logging.info(
            "Ran %s in %f s",
            func.__name__,
            round(time.perf_counter() - start, round_to),
        )
        return res

    return wrapper
