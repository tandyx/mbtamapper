"""for typing constants"""

import typing as t

# import pytz
from sqlalchemy.dialects.sqlite import DATETIME

# 20250518
SQLA_GTFS_DATE = DATETIME(storage_format="%(year)04d%(month)02d%(day)02d")


TimeZones = t.Literal["America/New_York"]


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


class GitInfoBase(t.TypedDict):
    """type definition for git info dictionary"""

    parent_commit: str
    message: str
    commiter: str
    # commit_date: str
    author: str
    author_date: str
    commit: str
    refs: str


class GitInfo(GitInfoBase, total=False):
    """type definition for git info dictionary with optional remote_url"""

    remote_url: str


# pylint: disable=line-too-long
class CacheConfigDict(t.TypedDict, total=False):
    """
    TypedDict for Flask-Caching configuration options.

    Each key is an optional configuration parameter for Flask-Caching.
    See Flask-Caching documentation for full details.
    """

    DEBUG: bool
    """Enable debug mode for Flask-Caching. Defaults to the value of Flask's DEBUG setting."""

    CACHE_TYPE: t.Literal[
        "NullCache",
        "SimpleCache",
        "FileSystemCache",
        "RedisCache",
        "RedisSentinelCache",
        "RedisClusterCache",
        "UWSGICache",
        "MemcachedCache",
        "SASLMemcachedCache",
        "SpreadSASLMemcachedCache",
    ]
    """Specifies which type of caching object to use. This is an import string that will be imported and instantiated. Built-in cache types: NullCache (default), SimpleCache, FileSystemCache, RedisCache, RedisSentinelCache, RedisClusterCache, UWSGICache, MemcachedCache, SASLMemcachedCache, SpreadSASLMemcachedCache."""

    CACHE_NO_NULL_WARNING: bool
    """Silence the warning message when using cache type of null."""

    CACHE_ARGS: list[t.Any]
    """Optional list to unpack and pass during the cache class instantiation."""

    CACHE_OPTIONS: dict[str, t.Any] | None
    """Optional dictionary to pass during the cache class instantiation."""

    CACHE_DEFAULT_TIMEOUT: int
    """The timeout that is used if no other timeout is specified. Unit of time is seconds. Defaults to 300."""

    CACHE_IGNORE_ERRORS: bool
    """If set, any errors that occurred during the deletion process will be ignored. Relevant for filesystem and simple backends. Defaults to False."""

    CACHE_THRESHOLD: int
    """The maximum number of items the cache will store before it starts deleting some. Used only for SimpleCache and FileSystemCache. Defaults to 500."""

    CACHE_KEY_PREFIX: str
    """A prefix that is added before all keys. Makes it possible to use the same memcached server for different apps. Used only for RedisCache and MemcachedCache. Defaults to flask_cache_."""

    CACHE_SOURCE_CHECK: bool
    """Controls if the source code of the function should be included when forming the hash used as the cache key. Ensures cache is invalidated if source changes. Defaults to False."""

    CACHE_UWSGI_NAME: str
    """The name of the uwsgi caching instance to connect to. Defaults to an empty string, which means uWSGI will cache in the local instance."""

    CACHE_MEMCACHED_SERVERS: list[str] | None
    """A list or tuple of server addresses. Used only for MemcachedCache."""

    CACHE_MEMCACHED_USERNAME: str
    """Username for SASL authentication with memcached. Used only for SASLMemcachedCache."""

    CACHE_MEMCACHED_PASSWORD: str
    """Password for SASL authentication with memcached. Used only for SASLMemcachedCache."""

    CACHE_REDIS_HOST: str
    """A Redis server host. Used only for RedisCache."""

    CACHE_REDIS_PORT: int
    """A Redis server port. Default is 6379. Used only for RedisCache."""

    CACHE_REDIS_PASSWORD: str
    """A Redis password for server. Used only for RedisCache and RedisSentinelCache."""

    CACHE_REDIS_DB: int
    """A Redis db (zero-based number index). Default is 0. Used only for RedisCache and RedisSentinelCache."""

    CACHE_REDIS_SENTINELS: list[str]
    """A list or tuple of Redis sentinel addresses. Used only for RedisSentinelCache."""

    CACHE_REDIS_SENTINEL_MASTER: str
    """The name of the master server in a sentinel configuration. Used only for RedisSentinelCache."""

    CACHE_REDIS_CLUSTER: str
    """A string of comma-separated Redis cluster node addresses. Used only for RedisClusterCache."""

    CACHE_DIR: str | None
    """Directory to store cache. Used only for FileSystemCache."""

    CACHE_REDIS_URL: str
    """URL to connect to Redis server. Example redis://user:password@localhost:6379/2. Supports redis://, rediss://, unix://. Used only for RedisCache."""
