"""Returns the directory name of the current file."""
import os


def return_dirname(file: str, levels: int = 3) -> str:
    """Returns the directory name of the current file.

    Args:
        file (str): The current file
        levels (int, optional): The number of levels to go up. Defaults to 3.
    Returns:
        str: The directory name of the current file
    """
    file = os.path.abspath(file)
    for _ in range(levels):
        file = os.path.dirname(file)
    return file
