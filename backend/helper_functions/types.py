"""for typing constants"""

from sqlalchemy.dialects.sqlite import DATETIME

# 20250518
SQLA_GTFS_DATE = DATETIME(storage_format="%(year)04d%(month)02d%(day)02d")
