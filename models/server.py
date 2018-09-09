from typing import TypeVar

from models.base import BaseModel


TServer = TypeVar("TServer", bound="Server")


class Server(BaseModel[str, TServer]):
    name: str
    actor: "Actor"

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.actor = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def write(self, msg):
        pass

    def flush(self):
        pass

    def __iter__(self):
        return [self]

    def get_key(self) -> str:
        return self.name

    def _set_key(self, new_key: str):
        self.name = new_key


# pylint: disable=wrong-import-position,unused-import,ungrouped-imports
# Import Actor at the end to break circular dependency between Actor and Server.
# We need it only for type-checking, and `if typing.TYPE_CHECKING` didn't seem to work.
from .actor import Actor
