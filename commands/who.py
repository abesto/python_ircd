from commands.base import Command
from message import Message as M
from numeric_responses import *
import db

class WhoCommand(Command):
    required_parameter_count = 1
    command = 'WHO'

    def from_client(self, mask, o=None):
        # TODO: The <mask> passed to WHO is matched against users' host, server,
        # real name and nickname if the channel <mask> cannot be found.
        # TODO: If the "o" parameter is passed only operators are returned according
        # to the <mask> supplied.
        # TODO: If there is a list of parameters supplied
        # with a WHO message, a RPL_ENDOFWHO MUST be sent
        # after processing each list item with <name> being
        # the item.

        resp = []
        if db.channel_exists(mask):
            channel = db.get_channel(mask)
            for channel_user in channel.users:
                resp.append(RPL_WHOREPLY(self.user, channel_user, str(channel)))
            resp.append(RPL_ENDOFWHO(self.user, str(channel)))
        return resp

