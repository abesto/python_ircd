from include.message import Message as M

from commands.base import Command


class QuitCommand(Command):
    required_parameter_count = 0
    command = 'QUIT'

    def from_user(self, message=None, *_):
        self.user.delete()
        self.actor.disconnect()
        return [M(self.actor, 'ERROR')]
