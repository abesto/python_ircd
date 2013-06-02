"Load, instantiate and call command handlers"

import importlib
import logging

from config import config
from models.actor import Actor

log = logging.getLogger(__name__)


class Error(Exception):
    pass


class Dispatcher:
    def __init__(self):
        self.handlers = {}

    def register(self, command):
        module = importlib.import_module('commands.' + command.lower())
        handler = module.__dict__[command.capitalize() + 'Command']()
        if command != handler.command:
            raise Error('Command mismatch. Incoming: %s. Handler: %s.'
            % (command, handler.command))
        self.handlers[handler.command] = handler

    def dispatch(self, socket, message):
        actor = Actor.by_socket(socket)
        message.target = config.get('server', 'servername')
        if message.command not in self.handlers:
            try:
                self.register(message.command)
            except ImportError, e:
                log.warning('Unknown command %s. Message was: %s. Error: %s'
                % (message.command, repr(message), e))
                return
        return self.handlers[message.command].handle(actor, message)
