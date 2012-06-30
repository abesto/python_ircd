from commands.base import Command
from message import Message as M


class PingCommand(Command):
    required_parameter_count = 1
    command = 'PING'

    def from_user(self, *args):
        return M(self.actor, 'PONG', *args)
