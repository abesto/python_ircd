from commands.base import Command
from message import Message as M
import db

class QuitCommand(Command):
    required_parameter_count = 0
    command = 'QUIT'

    def from_client(self, message=None):
        db.disconnected(self.user.nickname)
        return [M(self.user, None, 'ERROR'), 'disconnect']