from include import Message as M
from include.numeric_responses import *

from models import Actor, ActorCollection, Channel, User

from commands.base import Command


class PrivmsgCommand(Command):
    required_parameter_count = 0
    command = 'PRIVMSG'

    def from_user(self, receivers=None, text=None, *_):
        if receivers is None:
            return ERR_NORECIPIENT(self.command, self.actor)
        if text is None:
            return ERR_NOTEXTTOSEND(self.actor)
        resp = []
        # TODO: check for ERR_TOOMANYTARGETS
        for receiver in receivers.split(','):
            if Channel.exists(receiver):
                users = [user
                         for user in Channel.get(receiver).users
                         if user is not self.user]
                resp.append(M(
                    ActorCollection(users),
                    self.command, receiver, text,
                    prefix=self.user))
            elif User.exists(receiver):
                resp.append(M(
                    Actor.by_user(User.get(receiver)),
                    User.get(receiver),
                    self.user.nickname, self.command, receiver, text))
            # TODO: Implement wildcards
            # TODO: check for ERR_WILDTOPLEVEL, RPL_AWAY, ERR_NOTOPLEVEL
            else:
                resp.append(ERR_NOSUCHNICK(receiver, self.actor))
        return resp
