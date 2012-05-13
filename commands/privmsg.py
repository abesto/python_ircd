from commands.base import Command
from message import Message as M
from numeric_responses import *
import db


class PrivmsgCommand(Command):
    required_parameter_count = 0
    command = 'PRIVMSG'

    def from_client(self, receivers=None, text=None):
        if receivers is None:
            return ERR_NORECIPIENT(self.command, self.user)
        if text is None:
            return ERR_NOTEXTTOSEND(self.socket)
        resp = []
        # TODO: check for ERR_TOOMANYTARGETS
        for receiver in receivers.split(','):
            if db.channel_exists(receiver):
                users = [user for user in db.get_channel(receiver).users if user is not self.user]
                resp.append(M(users, self.user, self.command, receiver, text))
            elif db.user_exists(receiver):
                resp.append(M(db.get_user(receiver), self.user.nickname, self.command, receiver, text))
            # TODO: Implement wildcards, check for ERR_WILDTOPLEVEL, RPL_AWAY, ERR_NOTOPLEVEL
            else:
                resp.append(ERR_NOSUCHNICK(receiver, self.user))
        return resp


