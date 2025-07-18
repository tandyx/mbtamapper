"""Module to hold decorators."""

import logging
import time
import traceback
import typing as t

from sqlalchemy.orm import scoped_session


def removes_session(_func: t.Callable[..., t.Any]):
    """Decorator to remove a scroped session from a Feed object after function call. \
    This decorator also removes the session from the object if an exception is raised.

    Args:
        - `_func (function)`: Function to wrap. \n
    Returns:
        - `function`: Wrapped function.
    """

    def _removes_session(*args, **kwargs):
        res = None
        exception: bool = False
        try:
            res = _func(*args, **kwargs)
        except Exception as err:  # pylint: disable=broad-except
            logging.error(
                "Error in %s: %s %s", _func.__name__, err, traceback.format_exc()
            )
            exception = True
        for arg in args:
            for attr_name in dir(arg):
                attr = getattr(arg, attr_name)
                if isinstance(attr, scoped_session):
                    attr.remove()
                    if exception:  # this may be a problem in the future;
                        attr.rollback()
                    return res
        return res

    return _removes_session


def timeit(_func: t.Callable[..., t.Any], round_to: int = 3, show_args: bool = True):
    """Decorator to time a function and log it.

    Args:
        - `_func (function)`: Function to wrap.
        - `round_to (int, optional)`: Number of decimal places to round to. Defaults to 3.
        - `show_args (bool, True)`: show args into the function\n
    Returns:
        - `function`: Wrapped function.
    """

    def _timeit(*args, **kwargs) -> t.Any:
        start = time.perf_counter()
        res = _func(*args, **kwargs)
        if show_args:
            _args = ", ".join(str(a) for a in args) if args else ""
            _kwargs = ", " + ", ".join(f"{k}={v}" for k, v in kwargs.items())
            logging.info(
                "Ran %s(%s) in %f s",
                _func.__name__,
                _args + (_kwargs if _kwargs != ", " else ""),
                round(time.perf_counter() - start, round_to),
            )
        else:
            logging.info(
                "Ran %s in %f s",
                _func.__name__,
                round(time.perf_counter() - start, round_to),
            )
        return res

    return _timeit


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
