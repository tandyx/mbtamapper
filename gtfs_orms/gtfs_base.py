"""Holds the base class for all GTFS elements"""
from typing import Any, Self, Type

from sqlalchemy import orm

from helper_functions import classproperty, is_json_searializable

# pylint: disable=unused-argument


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
    __realtime_name__: str
    # __table_args__ = {"sqlite_autoincrement": False, "sqlite_with_rowid": False}

    # primary_keys: list[str] = [key for key in __class__.__table__.columns if key.primary_key]
    # pylint: disable=no-self-argument
    @classproperty
    def primary_keys(cls: Type[Self]) -> list[str]:
        """Returns a list of string columns as the primary keys for the class as a property.

        Args:
            cls (Type[Self]): class to get primary keys from
        Returns:
            list[Column]: list of primary keys
        """
        return [key.name for key in cls.__table__.columns if key.primary_key]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({', '.join(key + '=' + str(getattr(self, key, None)) for key in self.primary_keys)})>"  # pylint: disable=line-too-long

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
            getattr(self, key) == getattr(other, key) for key in self.primary_keys
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
            getattr(self, key) < getattr(other, key) for key in self.primary_keys
        )

    def __hash__(self) -> int:
        """Implements hash operator."""

        return hash(tuple(getattr(self, key) for key in self.primary_keys))

    def __bool__(self) -> bool:
        """Implements bool operator. \\
            Also represents whether the object is valid to be added to the database."""

        return all(getattr(self, key, None) is not None for key in self.primary_keys)

    def as_json(self, *args, **kwargs) -> dict[str, Any]:
        """Returns a json searizable representation of \
            the object as opposed to Base.as_dict() which returns a dict.
            
        Args:
            *args: unused, but can be used in overriden methods to \
                pass in additional arguments
            **kwargs: unused, but can be used in overriden methods to \
                pass in additional arguments
        Returns:
            dict[str, Any]: json searizable representation of the object
        """

        return {
            k: v
            for k, v in self.__dict__.items()
            if k != "_sa_instance_state" and is_json_searializable(v)
        }

    def as_dict(self, *args, **kwargs) -> dict[str, Any]:
        """Returns a dict representation of the object, front-facing.\
        Override this method to change the dict representation.
        
        Args:
            *args: unused, but can be used in overriden methods to \
                pass in additional arguments
            **kwargs: unused, but can be used in overriden methods to \
                pass in additional arguments
        Returns:
            dict[str, Any]: dict representation of the object
        """

        new_dict = self.__dict__.copy()
        if "_sa_instance_state" in new_dict:
            del new_dict["_sa_instance_state"]
        return new_dict
