"""database_ops.py"""
import os
import logging
from datetime import datetime


def delete_old_databases(date: datetime, file_path: str = "") -> None:
    """Deletes files older than 4 days from the given path and date.

    Args:
        current_date (datetime): date to compare against (default: current date)
        file_path (str): path to delete files from (default: current directory)
    """
    for file in os.listdir(file_path):
        file_path = os.path.join(file_path, file)
        if (
            not file.endswith(".db")
            or not os.path.getmtime(file_path) < date.timestamp() - 345600
        ):
            continue
        os.remove(file_path)
        logging.info("Deleted file %s", file)
