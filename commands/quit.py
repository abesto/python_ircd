from commands.base import Command
from message import Message as M


class QuitCommand(Command):
    required_parameter_count = 0
    command = 'QUIT'

    def from_client(self, message=None):
        self.db.disconnected(self.user.nickname)
        return [M(self.user, 'ERROR'), 'disconnect']
