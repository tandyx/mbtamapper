"""Module to hold decorators."""
import logging
import time

from sqlalchemy.orm import scoped_session


def removes_session(func):
    """Decorator to remove a scroped session from a Feed object after function call."""

    def wrapper(*args, **kwargs):
        """Wrapper for decorator."""
        res = func(*args, **kwargs)
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
