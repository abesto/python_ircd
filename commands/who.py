from commands.base import Command
from numeric_responses import *

import abnf

class WhoCommand(Command):
    required_parameter_count = 1
    command = 'WHO'

    def from_client(self, mask, o=None):
        # TODO: If the "o" parameter is passed only operators are returned according
        # to the <mask> supplied.
        # TODO: If there is a list of parameters supplied
        # with a WHO message, a RPL_ENDOFWHO MUST be sent
        # after processing each list item with <name> being
        # the item.

        resp = []
        if self.db.channel_exists(mask):
            channel = self.db.get_channel(mask)
            for channel_user in channel.users:
                resp.append(RPL_WHOREPLY(self.user, channel_user, str(channel)))
        else:
            parser = abnf.wildcard(mask)
            for user in self.db.users:
                # TODO: add check for servername
                if any([abnf.parse(str, parser) for str in [user.hostname, user.realname, user.nickname]]):
                    resp.append(RPL_WHOREPLY(self.user, user, mask))
        #resp.append(RPL_ENDOFWHO(self.user, str(channel)))
        return resp

