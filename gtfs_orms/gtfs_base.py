"""Holds the base class for all GTFS elements"""
from typing import Any, Generator, Self

from sqlalchemy import Column, orm


class GTFSBase(orm.DeclarativeBase):
    """Base class for all GTFS elements

    Attributes:
        __tablename__ (str): name of the table
        __table_args__ (dict[str, Any]): table arguments
        __filename__ (str): name of the associated txt file, if applicable
        __realtime_name__ (str): name of the realtime operation in LinkedDatasets, if applicable
    """

    __filename__: str
    __realtime_name__: str
    # __table_args__ = {"sqlite_autoincrement": False, "sqlite_with_rowid": False}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({''.join(key.name + '=' + str(getattr(self, key.name, None)) for key in self._get_primary_keys())})>"  # pylint: disable=line-too-long

    def __str__(self) -> str:
        return str(self.as_dict())

    def __eq__(self, other: Self) -> bool:
        """Implements equality operator.

        Returns:
            bool: whether the objects are equal
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        return all(
            getattr(self, key.name) == getattr(other, key.name)
            for key in self._get_primary_keys()
        )

    def __lt__(self, other: Self) -> bool:
        """Implements less than operator.

        Returns:
            bool: whether the object is less than the other
        """
        if not isinstance(other, self.__class__):
            raise NotImplementedError(
                f"Cannot compare {self.__class__} to {other.__class__}"
            )
        return all(
            getattr(self, key.name) < getattr(other, key.name)
            for key in self._get_primary_keys()
        )

    def _get_primary_keys(self) -> Generator[Column, None, None]:
        """Returns the primary keys of the table.

        Returns:
            Generator[Column, None, None]: primary keys of the table
        """

        return (c for c in self.__table__.columns if c.primary_key)

    def _as_dict(self) -> dict[str, Any]:
        """Returns a dict representation of the object.\
            Internal method, do not override, and can be used within \
            overriden as_dict method.

        Returns:
            dict[str, Any]: dict representation of the object
        """
        class_dict = self.__dict__
        if "_sa_instance_state" in class_dict:
            del class_dict["_sa_instance_state"]
        return class_dict

    def is_valid(self) -> bool:
        """Returns whether the object is valid.

        Returns:
            bool: whether the object is valid
        """
        return all(getattr(self, key.name, None) for key in self._get_primary_keys())

    def as_dict(self) -> dict[str, Any]:
        """Returns a dict representation of the object, front-facing.\
        Override this method to change the dict representation.

        Returns:
            dict[str, Any]: dict representation of the object
        """
        return self._as_dict()
