"""Threader function."""
from threading import Thread
from typing import Callable


def threader(func: Callable, join: bool = False, *args, **kwargs) -> None:
    """Threader function.

    Args:
        func (Callable): Function to thread.
        join (bool, optional): Whether to join thread. Defaults to False.
        *args: Arguments for func.
        **kwargs: Keyword arguments for func.
    """

    job_thread = Thread(target=func, args=args, kwargs=kwargs)
    job_thread.start()
    if join:
        job_thread.join()
