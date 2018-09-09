from typing import TypeVar

from models.base import BaseModel


TServer = TypeVar("TServer", bound="Server")


class Server(BaseModel[str, TServer]):
    name: str

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def __str__(self):
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
