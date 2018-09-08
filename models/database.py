from typing import TypeVar, Type, List

from models import Error
from models.base import BaseModel

TKey = TypeVar("TKey")
TValue = TypeVar("TValue", bound=BaseModel)


class Database:
    """Simple in-memory key-value database for models of the IRC server"""

    def __init__(self):
        self.objects = {}

    def get(self, cls: Type[BaseModel[TKey]], key: TKey) -> TValue:
        """Look up a model instance by key"""
        if not self.exists(cls, key):
            raise Error("%s with key %s does not exist" % (cls.__name__, key))
        return self.objects[cls][key]

    def all(self, cls: Type[TValue]) -> List[TValue]:
        """Get all instances of the BaseModel subclass this method is called on"""
        if cls not in self.objects:
            self.objects[cls] = {}
        return list(self.objects[cls].values())

    def exists(self, cls: Type[BaseModel[TKey]], key: TKey) -> bool:
        """Check whether a model exists for the given key"""
        return cls in self.objects and key in self.objects[cls]

    def delete(self, cls: Type[BaseModel[TKey]], key: TKey):
        """Remove the instance from the database"""
        if cls in self.objects:
            del self.objects[cls][key]

    def save(self, model: BaseModel[TKey]):
        """Save the instance into the database"""
        cls = model.__class__
        key = model.get_key()
        exists = self.exists(cls, key)
        not_self = exists and self.get(cls, key) is not model
        if not_self:
            raise Error(
                "%s with key %s already exists but "
                "is not the object to be saved" % (cls.__name__, key)
            )
        if cls not in self.objects:
            self.objects[cls] = {}
        self.objects[cls][key] = model
        return model


DEFAULT_DATABASE = Database()
