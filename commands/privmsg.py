from commands.base import Command
from numeric_responses import *
from message import Message as M


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
            if self.db.channel_exists(receiver):
                users = [user
                         for user in self.db.get_channel(receiver).users
                         if user is not self.user]
                resp.append(M(
                    users,
                    self.command, receiver, text,
                    prefix=self.user))
            elif self.db.user_exists(receiver):
                resp.append(M(
                    self.db.get_user(receiver),
                    self.user.nickname, self.command, receiver, text))
            # TODO: Implement wildcards
            # TODO: check for ERR_WILDTOPLEVEL, RPL_AWAY, ERR_NOTOPLEVEL
            else:
                resp.append(ERR_NOSUCHNICK(receiver, self.user))
        return resp
