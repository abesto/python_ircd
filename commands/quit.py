from include.message import Message as M

from commands.base import Command
from models.actorcollection import ActorCollection


class QuitCommand(Command):
    required_parameter_count = 0
    command = 'QUIT'

    def from_user(self, message='leaving', *_):
        ret = []
        for channel in self.user.channels:
            channel.part(self.user)
            ret.append(
                M(ActorCollection(channel.users), 'PART', str(channel), message, prefix=str(self.user))
            )
        self.user.delete()
        self.actor.disconnect()
        return ret + [M(self.actor, 'ERROR')]
