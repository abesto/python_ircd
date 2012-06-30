from include import Message as M

from commands.base import Command


class PingCommand(Command):
    required_parameter_count = 1
    command = 'PING'

    def from_user(self, *args):
        return M(self.actor, 'PONG', *args)
