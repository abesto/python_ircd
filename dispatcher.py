import importlib
import logging

from db.memory_database import MemoryDatabase
from config import config

log = logging.getLogger(__name__)


class Error(Exception):
    pass

handlers = {}
db = MemoryDatabase()


def register(command):
    module = importlib.import_module('commands.' + command.lower())
    handler = module.__dict__[command.capitalize() + 'Command'](db)
    if command != handler.command:
        raise Error('Command mismatch. Incoming: %s. Handler: %s.'
        % (command, handler.command))
    handlers[handler.command] = handler


def dispatch(socket, message):
    message.target = config.get('server', 'servername')
    if message.command not in handlers:
        try:
            register(message.command)
        except ImportError:
            log.warning('Unknown command %s. Message was: %s'
            % (message.command, repr(message)))
            return
    return handlers[message.command].handle(socket, message)
