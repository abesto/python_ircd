from include.numeric_responses import *
from include.message import Message as M

import models
from models.channel import Channel
from models.actorcollection import ActorCollection

from commands.base import Command


class JoinCommand(Command):
    required_parameter_count = 1
    command = 'JOIN'

    def from_user(self, channels, keys='', *_):
        if channels == '0':
            # TODO: part all channels
            return
        channels = channels.split(',')
        keys = keys.split(',')

        ret = []

        # TODO: key handling
        for channel_name in channels:
            if Channel.exists(channel_name):
                channel = Channel.get(channel_name)
            else:
                try:
                    channel = Channel(channel_name)
                    channel.save()
                except models.Error:
                    ret.append(ERR_NOSUCHCHANNEL(channel_name, self.actor))
                    continue
            channel.join(self.user)
            ret.append(M(
                ActorCollection(channel.users),
                'JOIN', str(channel), prefix=self.user))
            ret.append(RPL_NAMEREPLY(self.actor, channel))
            # TODO: do we need to send RPL_ENDOFNAMES?
            ret.append(RPL_ENDOFNAMES(self.actor))
            if channel.topic is not None:
                ret.append(RPL_TOPIC(self.actor, channel))

        return ret
