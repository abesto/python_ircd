"""
`BaseModel`: base class for all models stored in the “database”
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Dict, Generic, Any

from models import Error


TKey = TypeVar("TKey")
TValue = TypeVar("TValue", bound="BaseModel")


class BaseModel(Generic[TKey, TValue], ABC):
    """Base blass for all models stored in the “database” `BaseModel.objects`"""

    objects: Dict[Any, Dict] = {}

    def __init__(self, key: TKey) -> None:
        self._set_key(key)

    def save(self: TValue) -> TValue:
        """Save the instance into the database"""
        from models import db

        return db.save(self)

    def delete(self):
        """Remove the instance from the database"""
        from models import db

        return db.delete(self.__class__, self.get_key())

    @abstractmethod
    def get_key(self) -> TKey:
        """Get the key for this model instance"""
        pass

    def set_key(self, new_key: TKey):
        """
        Set the key for this model instance, updating the database, and
        making sure the new key is not already taken
        """
        from models import db

        if db.exists(self.__class__, new_key):
            raise Error(
                "%s with key %s already exists" % (self.__class__.__name__, new_key)
            )
        if self.get_key() == new_key:
            pass
        self.delete()
        old_key = self.get_key()
        self._set_key(new_key)
        if self.get_key() != new_key:
            raise Error(
                "subclass was expected to change key from %s to %s, "
                "but key is not %s" % (old_key, new_key, self.get_key())
            )
        self.save()

    @abstractmethod
    def _set_key(self, new_key):
        """Update the key on the instance"""
        pass
