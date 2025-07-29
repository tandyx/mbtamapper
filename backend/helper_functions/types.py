"""for typing constants"""

import typing as t

from sqlalchemy.dialects.sqlite import DATETIME

# 20250518
SQLA_GTFS_DATE = DATETIME(storage_format="%(year)04d%(month)02d%(day)02d")


class RouteKey(t.TypedDict):
    """Route key type definition."""

    _key: str
    title: str
    description: str
    icon: str
    image: str
    fa_unicode: str
    display_name: str
    color: str
    route_types: list[str]
    sort_order: int


class RouteKeys(t.TypedDict):
    """Route keys type definition."""

    subway: RouteKey
    rapid_transit: RouteKey
    commuter_rail: RouteKey
    bus: RouteKey
    ferry: RouteKey
    all_routes: RouteKey
