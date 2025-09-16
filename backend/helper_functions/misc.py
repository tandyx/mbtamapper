"""miscellaneous helper functions that i'm too lazy to fit elsewhere"""

import subprocess

import gitinfo

from .types import GitInfo


def get_gitinfo() -> GitInfo:
    """Get git information about the current repository

    Returns:
        GitInfo: A dictionary containing git information
    """

    return gitinfo.get_git_info() | {
        "remote_url": subprocess.run(
            ["git", "remote", "get-url", "origin"], check=False, capture_output=True
        )
        .stdout.decode("utf-8")
        .strip()
    }
