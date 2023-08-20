"""Logging helper functions"""
import logging
from logging import Logger, Formatter, StreamHandler
from typing import Any


class LoggingFormatter(Formatter):
    """Logging Formatter"""

    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    # FORMAT = (
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    # )
    FORMAT = "[%(levelname)s] %(message)s "

    FORMATS = {
        logging.DEBUG: BLUE + FORMAT + RESET,
        logging.INFO: BLUE + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def __setattr__(self, __name: str, __value: Any) -> None:
        return super().__setattr__(__name, __value)

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def instantiate_logger(
    logger: Logger, level: int = None, formatter: Formatter = None
) -> None:
    """Instantiates logger with custom formatter

    Args:
        logger (Logger): logger to instantiate
        level (int, enum.CONST): logging level, defaults to logging.INFO
        Formatter (Formatter): custom formatter, defaults to LoggingFormatter
    """

    if not formatter:
        formatter = LoggingFormatter()
    if level is None or not isinstance(level, int):
        level = logging.INFO

    logger.setLevel(level)
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
