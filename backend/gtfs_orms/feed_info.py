"""File to hold the FeedInfo class and its associated methods."""

import datetime as dt
import typing as t

from sqlalchemy.orm import Mapped, mapped_column

from ..helper_functions.types import SQLA_GTFS_DATE
from .base import Base


class FeedInfo(Base):
    """FeedInfo

    describes general info about the feed

    https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs.md#feed_infotxt

    """

    __tablename__ = "feed_info"
    __filename__ = "feed_info.txt"

    feed_publisher_name: Mapped[str]
    feed_publisher_url: Mapped[str]
    feed_lang: Mapped[str]
    feed_start_date: Mapped[t.Optional[dt.datetime]] = mapped_column(SQLA_GTFS_DATE)
    feed_end_date: Mapped[t.Optional[dt.datetime]] = mapped_column(SQLA_GTFS_DATE)
    feed_version: Mapped[t.Optional[str]]
    feed_contact_email: Mapped[t.Optional[str]]
    feed_id: Mapped[str] = mapped_column(primary_key=True)
