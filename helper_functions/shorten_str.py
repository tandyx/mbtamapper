"""Shortens a string to a certain length."""


def shorten(string: str, length: int = 20, suffix: str = "...") -> str:
    """Shortens a string to a certain length.

    Args:
        string (str): String to shorten.
        length (int, optional): Length to shorten to. Defaults to 20.
        suffix (str, optional): Suffix to add to the end of the string. Defaults to "...".
    Returns:
        str: Shortened string.
    """
    return (string[:length] + suffix) if len(string) > length else string
