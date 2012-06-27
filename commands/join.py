from commands.base import Command
from numeric_responses import *
import models
from message import Message as M


class JoinCommand(Command):
    required_parameter_count = 1
    command = 'JOIN'

    def from_client(self, channels, keys=''):
        if channels == '0':
            # TODO: part all channels
            return
        channels = channels.split(',')
        keys = keys.split(',')

        ret = []

        # TODO: key handling
        for channel_name in channels:
            try:
                channel = self.db.get_channel(channel_name)
                channel.join(self.user)
                ret.append(M(
                    channel.users, 'JOIN', str(channel), prefix=self.user))
                ret.append(RPL_NAMEREPLY(self.user, channel))
                # TODO: do we need to send RPL_ENDOFNAMES?
                ret.append(RPL_ENDOFNAMES(self.user))
                if channel.topic is not None:
                    ret.append(RPL_TOPIC(self.user, channel))
            except models.Error:
                ret.append(ERR_NOSUCHCHANNEL(channel_name, self.user))

        return ret
