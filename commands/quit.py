from commands.base import Command
from message import Message as M


class QuitCommand(Command):
    required_parameter_count = 0
    command = 'QUIT'

    def from_user(self, message=None):
        self.user.delete()
        return [M(self.actor, 'ERROR'), 'disconnect']
