import logging
from abc import ABC

from include.connection import Connection
from include.message import Message
from models import Error
from models.base import BaseModel

log = logging.getLogger(__name__)


class Actor(BaseModel, ABC):
    connection: Connection

    def __init__(self, connection: Connection, **kwargs) -> None:
        self.password = None
        self.disconnected = False
        self.connection_dropped = False
        self.connection = connection

        self._server = None
        self._user = None
        if "user" in kwargs:
            self.user = kwargs["user"]
        if "server" in kwargs:
            self.server = kwargs["server"]

    # Model stuff
    def get_key(self):
        return self.connection

    @staticmethod
    def by_connection(connection: Connection):
        try:
            return Actor.get(connection)
        except Error:
            actor = Actor(connection)
            actor.save()
            return actor

    @staticmethod
    def by_user(user):
        return user.actor

    # Union of User and Server
    def is_user(self):
        return self._user is not None

    def is_server(self):
        return self._server is not None

    def get_user(self):
        if not self.is_user():
            raise Error("not a user")
        return self._user

    def get_server(self):
        if not self.is_server():
            raise Error("not a server")
        return self._server

    def __setattr__(self, key, value):
        if key == "server":
            if self.is_user():
                raise Error("user XOR server must be passed to Actor")
            if value.actor:
                raise Error("server already has an actor set")
            self._server = value
            self._server.actor = self
        elif key == "user":
            if self.is_server():
                raise Error("user XOR server must be passed to Actor")
            if hasattr(value, "actor"):
                raise Error("user already has an actor set")
            self._user = value
            self._user.actor = self
        else:
            super(BaseModel, self).__setattr__(key, value)

    def __str__(self):
        if self.is_user():
            return "Actor(" + str(self.get_user()) + ")"
        elif self.is_server():
            return "Actor(" + str(self.get_server()) + ")"
        else:
            return "Unknown Actor"

    def __repr__(self):
        return str(self)

    # Implement socket-like interface
    def write(self, message: Message):
        if self.is_user() and message.add_nick:
            message.parameters.insert(0, self.get_user().nickname)
        try:
            self.connection.write(message)
        except:
            self.connection_dropped = True
            log.exception("Connection dropped for {}, write() call failed".format(self))

        if self.is_user() and message.add_nick:
            message.parameters = message.parameters[1:]

    async def flush(self):
        try:
            return await self.connection.drain()
        except:
            self.connection_dropped = True
            log.exception("Connection dropped for {}, flush() call failed".format(self))

    def disconnect(self):
        self.disconnected = True

    def __iter__(self):
        return iter([self])
