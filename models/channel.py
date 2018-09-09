""""
`ChannelMode`: represents mode flags for a channel
`Channel`: guess what that is.
"""
from typing import TypeVar, List, Optional

from include import abnf
from models import Error, User
from models.base import BaseModel

TChannel = TypeVar("TChannel", bound="Channel")


# pylint: disable=too-few-public-methods
class ChannelMode:
    """Represents mode flags for a channel"""

    def __init__(self):
        self.distributed = True
        self.invite_only = False


# pylint: enable=too-few-public-methods


class Channel(BaseModel[str, TChannel]):
    """An IRC Channel. D'uh."""

    prefix: str
    channelid: Optional[str]
    name: str
    users: List[User]

    def __init__(self, name: str) -> None:
        super().__init__(name)
        if not self.is_valid_name(name):
            raise Error("Erroneous channel name")

        self.mode = ChannelMode()
        self.users = []
        self.topic = None

    def __str__(self):
        return self.prefix + self.name

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Verifies that a string is a valid channel name"""
        return bool(abnf.default_parser().parse_channel(name))

    def get_key(self):
        return str(self)

    def join(self, user: User) -> None:
        """Adds a `User` to the list of users in this channel"""
        if user not in self.users:
            self.users.append(user)
            user.join(self)

    def part(self, user: User) -> None:
        """Removes a `User` from the list of users in this channel"""
        if user in self.users:
            self.users.remove(user)
            user.part(self)

    def _set_key(self, new_key):
        raw = abnf.default_parser().parse_channel(new_key)
        self.prefix = raw[0]
        self.channelid = raw[1] if self.prefix == "!" else None
        self.name = raw[2] if self.prefix == "!" else raw[1]
