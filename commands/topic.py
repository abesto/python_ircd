from commands.base import Command
from numeric_responses import *
import db

class TopicCommand(Command):
    required_parameter_count = 1
    command = 'TOPIC'

    def from_client(self, channel, topic=None):
        # TODO: ERR_NOCHANMODES, ERR_CHANOPRIVSNEEDED
        channel = db.get_channel(channel)
        if self.user not in channel.users:
            return ERR_NOTONCHANNEL(user, channel)
        if topic is None:
            if channel.topic is None:
                return RPL_NOTOPIC(self.user, channel)
            else:
                return RPL_TOPIC(self.user, channel)
        elif topic == '':
            channel.topic = None
        else:
            channel.topic = topic
        # Forward message to others on the channel
        self.message.target = channel.users
        return self.message

