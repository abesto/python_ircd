from typing import List

from commands.base import Command
from include.numeric_responses import *
from models import db, ActorCollection, Channel


class TopicCommand(Command):
    required_parameter_count = 1
    command = "TOPIC"

    def from_user(self, channel_name, topic=None, *_):
        # TODO: ERR_NOCHANMODES, ERR_CHANOPRIVSNEEDED
        if not db.exists(Channel, channel_name):
            return ERR_NOSUCHCHANNEL(channel_name, self.actor)
        channel = db.get(Channel, channel_name)
        if self.user not in channel.users:
            return ERR_NOTONCHANNEL(channel_name, self.actor)
        if topic is None:
            if channel.topic is None:
                return RPL_NOTOPIC(self.actor, channel)
            else:
                return RPL_TOPIC(self.actor, channel)
        elif topic == "":
            channel.topic = None
        else:
            channel.topic = topic
        # Forward message to others on the channel
        self.message.target = ActorCollection(channel.users)
        return self.message

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
