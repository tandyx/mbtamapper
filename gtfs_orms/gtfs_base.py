"""Holds the base class for all GTFS elements"""

import json
from typing import Any, Self, Type

from sqlalchemy import orm

from helper_functions import classproperty

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

    def as_json(self, *include, **kwargs) -> dict[str, Any]:
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
            for k, v in self.as_dict(*include).items()
            if not k.startswith("_") and _is_json_searializable(v)
        }

    def as_json_dict(self) -> dict[str, Any]:
        """Returns a dict representation of the object
        
        args:
            - `*include`: other orm attars to include within the dict
            - `**kwargs`: unused, but can be used in overriden methods to \
                pass in additional arguments \n
        returns:
            - `dict[str, Any]`: dict representation of the object
        """

        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and _is_json_searializable(v)
        }

    def as_dict(self, *include, **kwargs) -> dict[str, Any]:
        """Returns a dict representation of the object, front-facing.\
        Override this method to change the `dict `representation.
        
        Args:
            - `*include`: other orm attars to include within the dict
            - `**kwargs`: unused, but can be used in overriden methods to \
                pass in additional arguments \n
        Returns:
            - `dict[str, Any]`: dict representation of the object
        """

        new_dict = self.__dict__.copy()
        if "_sa_instance_state" in new_dict:
            del new_dict["_sa_instance_state"]
        for attr in include:
            if not hasattr(self, attr):
                continue
            attar_val = getattr(self, attr)
            if isinstance(attar_val, GTFSBase):
                new_dict[attr] = attar_val.as_json_dict()
            if isinstance(attar_val, list):
                new_dict[attr] = [
                    d.as_json_dict() if isinstance(d, GTFSBase) else d
                    for d in attar_val
                ]
        return new_dict


def _is_json_searializable(obj: Any) -> bool:
    """Checks if an object is JSON serializable.

    Args:
        - `obj (Any)`: Object to check. \n
    Returns:
        - `bool`: Whether the object is JSON serializable.
    """
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False
