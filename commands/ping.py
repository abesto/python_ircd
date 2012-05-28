from commands.base import Command
from message import Message as M


class PingCommand(Command):
    required_parameter_count = 1
    command = 'PING'

    def from_client(self, *args):
        return M(self.socket.client, 'PONG', *args)
