from include.numeric_responses import *

import models
from models.channel import Channel
from models.actorcollection import ActorCollection

from commands.base import Command


class TopicCommand(Command):
    required_parameter_count = 1
    command = 'TOPIC'

    def from_user(self, channel_name, topic=None, *_):
        # TODO: ERR_NOCHANMODES, ERR_CHANOPRIVSNEEDED
        if not Channel.exists(channel_name):
            return ERR_NOSUCHCHANNEL(channel_name, self.actor)
        channel = Channel.get(channel_name)
        if self.user not in channel.users:
            return ERR_NOTONCHANNEL(channel_name, self.actor)
        if topic is None:
            if channel.topic is None:
                return RPL_NOTOPIC(self.actor, channel)
            else:
                return RPL_TOPIC(self.actor, channel)
        elif topic == '':
            channel.topic = None
        else:
            channel.topic = topic
        # Forward message to others on the channel
        self.message.target = ActorCollection(channel.users)
        return self.message
