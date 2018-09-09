"""
`ActorCollection`: multiplexes writes and other operations to multiple `Actor` instances
`Error`: class of all exceptions thrown due to caller / logic errors
"""

import asyncio

from include.message import Message
from models import Actor, Server, User, Error as ModelsError


class Error(ModelsError):
    """Caller / logic error in ActorCollection"""

    pass


class ActorCollection:
    """Multiplexes writes and other operations to multiple `Actor` instances"""

    def __init__(self, children):
        self.children = set()
        for child in children:
            if isinstance(child, Actor):
                self.children.add(child)
            elif isinstance(child, (User, Server)):
                self.children.add(child.actor)
            elif isinstance(child, ActorCollection):
                self.children += child.children
            else:
                raise Error("Don't know what to do with %s" + child.__class__)
        self.children = frozenset(self.children)

    def write(self, message: Message):
        """Writes `message` to all `Actor`s in this collection"""
        for child in self.children:
            child.write(message)

    def flush(self):
        """Flushes the writers of all `Actor`s in this collection"""
        return asyncio.wait([child.flush() for child in self.children])

    def disconnect(self):
        """Disconnects the connections of all `Actor`s in this collection"""
        for child in self.children:
            child.disconnect()

    # pylint: disable=no-self-use
    def read(self):
        """Read doesn't make sense on an `ActorCollection`"""
        raise Error("read is undefined on ActorCollection")

    # pylint: enable=no-self-use

    def __str__(self):
        return (
            "ActorCollection("
            + ", ".join([str(child) for child in self.children])
            + ")"
        )

    def __repr__(self):
        return (
            "ActorCollection("
            + ", ".join([repr(child) for child in self.children])
            + ")"
        )

    def __eq__(self, other):
        if isinstance(other, ActorCollection):
            return all([actor in other for actor in self.children])
        return NotImplemented

    def __contains__(self, item):
        return item in self.children

    def __iter__(self):
        return iter(self.children)

    def __hash__(self):
        return hash(self.children)
