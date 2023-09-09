"Holds the base class for all GTFS elements"
from sqlalchemy.orm import DeclarativeBase


class GTFSBase(DeclarativeBase):
    "Base class for all GTFS elements"

    __table_args__ = {"sqlite_autoincrement": False, "sqlite_with_rowid": False}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.__dict__})>"

    def __str__(self) -> str:
        return self.__repr__()
