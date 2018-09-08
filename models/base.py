from typing import List, TypeVar, Type, Dict, Any

from models import Error


T = TypeVar("T", bound="BaseModel")


class BaseModel:
    objects: Dict[Any, Any] = {}

    @classmethod
    def get(cls, key):
        if not cls.exists(key):
            raise Error("%s with key %s does not exist" % (cls.__name__, key))
        return BaseModel.objects[cls][key]

    @classmethod
    def all(cls: Type[T]) -> List[T]:
        if cls not in BaseModel.objects:
            BaseModel.objects[cls] = {}
        return list(BaseModel.objects[cls].values())

    @classmethod
    def exists(cls, key):
        return cls in BaseModel.objects and key in BaseModel.objects[cls]

    def save(self):
        exists = self.__class__.exists(self.get_key())
        not_self = exists and self.__class__.get(self.get_key()) is not self
        if not_self:
            raise Error(
                "%s with key %s already exists but "
                "is not the object to be saved"
                % (self.__class__.__name__, self.get_key())
            )
        if not self.__class__ in BaseModel.objects:
            BaseModel.objects[self.__class__] = {}
        BaseModel.objects[self.__class__][self.get_key()] = self

    def delete(self):
        if self.__class__ in BaseModel.objects:
            del BaseModel.objects[self.__class__][self.get_key()]

    def get_key(self):
        raise NotImplementedError

    def set_key(self, new_key):
        if self.__class__.exists(new_key):
            raise Error(
                "%s with key %s already exists" % (self.__class__.__name__, new_key)
            )
        if self.get_key == new_key:
            pass
        del BaseModel.objects[self.__class__][self.get_key()]
        old_key = self.get_key()
        self._set_key(new_key)
        if self.get_key() != new_key:
            raise Error(
                "subclass was expected to change key from %s to %s, "
                "but key is not %s" % (old_key, new_key, self.get_key())
            )
        self.save()

    def _set_key(self, new_key):
        raise NotImplementedError
