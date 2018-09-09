"""
`Dispatcher`: Load, instantiate, and call command handlers
"""

import importlib
import logging
from typing import List
from pydispatch import dispatcher

from config import config
from include.connection import Connection, SelfConnection
from include.message import Message
from models import db, Actor, Error as ModelsError, Server

LOG = logging.getLogger(__name__)


class Error(ModelsError):
    """Represents errors raised by `Dispatcher`"""

    pass


class Dispatcher:
    """Load, instantiate, and call command handlers"""

    def __init__(self):
        self.handlers = {}

    def register(self, command: str):
        """Create and record a `Command` subclass that will handle the IRC command `command`"""
        module = importlib.import_module("commands." + command.lower())
        handler = module.__dict__[command.capitalize() + "Command"]()
        if command != handler.command:
            raise Error(
                "Command mismatch. Incoming: %s. Handler: %s."
                % (command, handler.command)
            )
        self.handlers[handler.command] = handler

    def dispatch(self, connection: Connection, message: Message) -> List[Message]:
        """
        Dispatch a `Message` received through a `Connection`
        to the right `Command` instance for handling
        """
        actor = db.get_or_create(Actor, connection)
        if message.command not in self.handlers:
            try:
                self.register(message.command)
            except ImportError as exc:
                LOG.warning(
                    "Unknown command %s. Message was: %s. Error: %s",
                    message.command,
                    repr(message),
                    exc,
                )
                raise Error("Unknown command: %s" % message.command)
        return self.handlers[message.command].handle(actor, message)
