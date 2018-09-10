"""
`PartCommand`: Implements the PART IRC command
"""
from typing import List

from commands.base import Command
from include.message import Message
from include.numeric_replies import ERR_NOSUCHCHANNEL, ERR_NOTONCHANNEL
from models import db, Channel, ActorCollection


class PartCommand(Command):
    """Implements the PART IRC command"""

    required_parameter_count = 1
    command = "PART"

    # pylint: disable=arguments-differ,keyword-arg-before-vararg
    def from_user(self, channels: str = "", msg: str = "leaving", *_) -> List[Message]:
        """
        For each channel in `channels`, send a PART message to everyone in the channel
        and remove the user from the user list of the channel (all this assuming
        the user is actually in the channel)
        """
        ret = []
        for channel_name in channels.split(","):
            if not db.exists(Channel, channel_name):
                ret.append(ERR_NOSUCHCHANNEL(channel_name, self.actor))
                continue
            channel = db.get(Channel, channel_name)
            if self.user not in channel.users:
                ret.append(ERR_NOTONCHANNEL(channel_name, self.actor))
                continue
            ret.append(
                Message(
                    ActorCollection(channel.users),
                    "PART",
                    str(channel),
                    msg,
                    prefix=str(self.user),
                )
            )
            self.user.part(channel)
        return ret

    # pylint: enable=arguments-differ,keyword-arg-before-vararg

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
