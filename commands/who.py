from typing import List

from commands.base import Command
from include import abnf
from include.numeric_responses import *
from models.channel import Channel
from models.user import User


class WhoCommand(Command):
    required_parameter_count = 1
    command = "WHO"

    def from_user(self, mask, o=None, *_):
        # TODO: If the "o" parameter is passed only operators are returned
        # according to the <mask> supplied.
        # TODO: If there is a list of parameters supplied
        # with a WHO message, a RPL_ENDOFWHO MUST be sent
        # after processing each list item with <name> being
        # the item.

        resp = []
        if Channel.exists(mask):
            channel = Channel.get(mask)
            for channel_user in channel.users:
                resp.append(RPL_WHOREPLY(self.actor, channel_user, str(channel)))
        else:
            if mask == "0":
                mask = "*"
            parser = abnf.wildcard(mask)
            for user in User.all():
                # TODO: add check for servername
                if any(
                    [
                        abnf.parse(str, parser)
                        for str in [user.hostname, user.realname, user.nickname]
                    ]
                ):
                    resp.append(RPL_WHOREPLY(self.actor, user, mask))
        # resp.append(RPL_ENDOFWHO(self.user, str(channel)))
        return resp

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
