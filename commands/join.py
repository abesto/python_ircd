from commands.base import Command
from numeric_responses import *
from message import Message as M
import db

class JoinCommand(Command):
    required_parameter_count = 1
    command = 'JOIN'

    def from_client(self, channels, keys=''):
        if channels == '0':
            # TODO: part all channels
            pass
        channels = channels.split(',')
        keys = keys.split(',')

        ret = []

        # TODO: key handling
        for channel_name in channels:
            try:
                channel = db.get_channel(channel_name)
                channel.join(self.user)
                ret.append(M(channel.users,'JOIN', str(channel), prefix=self.user))
                ret.append(RPL_NAMEREPLY(self.user, channel))
                ret.append(RPL_ENDOFNAMES(self.user))
                if channel.topic is not None:
                    ret.append(RPL_TOPIC(self.user, channel))
            except db.Error:
                ret.append(ERR_NOSUCHCHANNEL(channel_name, self.user))

        return ret
