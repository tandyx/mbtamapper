"""Helper function to download a zip file from a url and extract it to a path."""
import io
import logging
import zipfile
import requests


def download_zip(url: str, file_path: str = "") -> None:
    """Downloads the gtfs zip file from the url.

    Args:
        url (str): url to download from
        file_path (str): path to extract to (default: current directory)

    Note that this function will create a file at file_path if one does not exist.
    """
    source = requests.get(url, timeout=10)
    with zipfile.ZipFile(io.BytesIO(source.content)) as zipfile_bytes:
        zipfile_bytes.extractall(file_path)
    logging.info("Downloaded zip from %s to %s", url, file_path)
