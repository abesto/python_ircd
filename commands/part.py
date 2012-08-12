from include.numeric_responses import *
from include.message import Message as M

import models
from models.channel import Channel
from models.actorcollection import ActorCollection

from commands.base import Command


class PartCommand(Command):
    required_parameter_count = 1
    command = 'PART'

    def from_user(self, channels, msg='leaving', *_):
        channels = channels.split(',')

        ret = []

        for channel_name in channels:
            if not Channel.exists(channel_name):
                ret.append(ERR_NOSUCHCHANNEL(channel_name, self.actor))
                continue
            channel = Channel.get(channel_name)
            if self.user not in channel.users:
                ret.append(ERR_NOTONCHANNEL(channel_name, self.actor))
                continue
            ret.append(M(ActorCollection(channel.users),
                         'PART', str(channel), msg,
                         prefix=str(self.user)
            ))
            self.user.part(channel)

        return ret
