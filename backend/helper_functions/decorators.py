"""Module to hold decorators."""

import functools
import logging
import time
import typing as t

if t.TYPE_CHECKING:
    from ..gtfs_loader.feed import Feed

# T = t.TypeVar("T", t.Callable[..., t.Any], t.Any)

P = t.ParamSpec("P")
R = t.TypeVar("R")


def removes_session(_func: t.Callable[P, R]) -> t.Callable[t.Concatenate[int, P], R]:
    """Decorator to remove a scroped session from a Feed object after function call. \
    This decorator also removes the session from the object if an exception is raised.

    Args:
        _func (function): Function to wrap.
    Returns:
        function: Wrapped function.
    """

    @functools.wraps(_func)
    def _removes_session(*args, **kwargs):
        self: "Feed" | None = args[0] if args else None
        try:
            return _func(*args, **kwargs)
        finally:
            if self is not None and hasattr(self, "scoped_session"):
                try:
                    self.scoped_session.remove()
                except Exception:  # pylint: disable=broad-exception-caught
                    # don't let cleanup errors mask the real error
                    logging.exception("failed to remove scoped_session")

    return _removes_session


# def removes_session(_func: T) -> t.Callable[t.Concatenate[int, P], R]:
#     """Decorator to remove a scroped session from a Feed object after function call. \
#     This decorator also removes the session from the object if an exception is raised.

#     Args:
#         _func (function): Function to wrap.

#     Returns:
#         function: Wrapped function.
#     """

#     def _removes_session(*args, **kwargs):
#         res = None
#         try:
#             res = _func(*args, **kwargs)
#         except Exception as err:  # pylint: disable=broad-except
#             logging.error(
#                 "Error in %s: %s %s", _func.__name__, err, traceback.format_exc()
#             )
#         return res

#     return _removes_session


def timeit(
    _func: t.Callable[P, R], round_to: int = 3, show_args: bool = True
) -> t.Callable[t.Concatenate[int, P], R]:
    """Decorator to time a function and log it.

    Args:
        _func (function): Function to wrap.
        round_to (int, optional): Number of decimal places to round to. Defaults to 3.
        show_args (bool, True): show args into the function
    Returns:
        function: Wrapped function.
    """

    @functools.wraps(_func)
    def _timeit(*args, **kwargs):
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
        property (property): property to wrap.
    Returns:
        property: Wrapped property."""

    def __get__(self, owner_self: object, owner_cls: object):
        """Gets the property.

        Args:
            owner_self (object): Owner object.
            owner_cls (object): Owner class.

        Returns:
            object: Value of property.
        """
        return self.fget(owner_cls)
