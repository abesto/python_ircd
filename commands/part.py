from typing import List

from commands.base import Command
from include.message import Message as M
from include.numeric_responses import *
from models import db, Channel, ActorCollection


class PartCommand(Command):
    required_parameter_count = 1
    command = "PART"

    def from_user(self, channels, msg="leaving", *_):
        channels = channels.split(",")

        ret = []

        for channel_name in channels:
            if not db.exists(Channel, channel_name):
                ret.append(ERR_NOSUCHCHANNEL(channel_name, self.actor))
                continue
            channel = db.get(Channel, channel_name)
            if self.user not in channel.users:
                ret.append(ERR_NOTONCHANNEL(channel_name, self.actor))
                continue
            ret.append(
                M(
                    ActorCollection(channel.users),
                    "PART",
                    str(channel),
                    msg,
                    prefix=str(self.user),
                )
            )
            self.user.part(channel)

        return ret

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
