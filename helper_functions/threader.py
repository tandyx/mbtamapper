"""Threader function."""
from threading import Thread
from typing import Callable


def threader(func: Callable, *args, join: bool = False, **kwargs) -> None:
    """Threader function.

    Args:
        func (Callable): Function to thread.
        *args: Arguments for func.
        join (bool, optional): Whether to join thread. Defaults to True.
        **kwargs: Keyword arguments for func.
    """

    job_thread = Thread(target=func, args=args, kwargs=kwargs)
    job_thread.start()
    if join:
        job_thread.join()
