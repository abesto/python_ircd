"""
`Message`: one parsed IRC message
"""
from typing import Optional, List, TypeVar, Type

from config import config
from include import abnf

TMessage = TypeVar("TMessage", bound="Message")


class Error(Exception):
    """Thrown when errors occur in `Message`"""

    pass


class Message:
    """One parsed IRC message"""

    target: "Target"
    command: str
    parameters: List[str]

    def __init__(
        self, target: "Target", command: str, *parameters: Optional[str], **kwargs
    ) -> None:
        self.command = command
        self.parameters = [x for x in parameters if x is not None]
        for parameter in self.parameters[:-1]:
            if " " in parameter:
                raise Error("Space can only appear in the very last parameter")
        self.target: "Target" = target
        self.prefix = str(kwargs["prefix"]) if "prefix" in kwargs else None
        self.add_nick = kwargs["add_nick"] if "add_nick" in kwargs else False

    @classmethod
    def from_string(cls: Type[TMessage], target: "Target", string: str) -> TMessage:
        """Parse a string into a `Message` object"""
        if len(string) > 512:
            raise Error("Message must not be longer than 512 characters")
        parser = abnf.default_parser()
        raw = parser.parse_message(string)
        if not isinstance(raw, list):
            raise Error('Failed to parse message: "{}"'.format(string))
        if config.get("parser", "lowercase_commands"):
            raw[1] = raw[1].upper()
        prefix = raw.pop(0)
        msg = cls(target, prefix=prefix, *raw)
        return msg

    def __str__(self):
        params = self.parameters[:]
        for param in params[:-1]:
            if param is not None and " " in param:
                raise Error("Space can only appear in the very last parameter")
        if params and " " in params[-1]:
            params[-1] = ":%s" % params[-1]
        return "{prefix}{command} {params}\r\n".format(
            prefix=":%s " % self.prefix if self.prefix is not None else "",
            command=str(self.command),
            params=" ".join(params),
        )

    def __repr__(self):
        return "'%s'" % str(self)[:-2]

    def __eq__(self, other):
        return (
            isinstance(other, Message)
            and self.prefix == other.prefix
            and self.command == other.command
            and self.parameters == other.parameters
            and self.target == other.target
        )


# pylint: disable=wrong-import-position,unused-import
# Import Target at the end to break circular dependency between Actor and Message
#  We need it only for type-checking, and `if typing.TYPE_CHECKING` didn't seem to work.
from models import Target
