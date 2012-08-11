from commands.base import Command
from models.user import User
from models.server import Server
from models.actorcollection import ActorCollection

from include import abnf
from include.message import Message as M
from include.numeric_responses import *

from _welcome import welcome


class NickCommand(Command):
    required_parameter_count = 0
    command = 'NICK'
    user_registration_command = True

    def from_user(self, to_nick=None, hopcount=None, *_):
        if to_nick is None:
            return ERR_NONICKNAMEGIVEN(self.actor)
        if len(to_nick) > 9 or abnf.parse(to_nick, abnf.nickname) != to_nick:
            return ERR_ERRONEUSNICKNAME(to_nick.replace(' ', '_'), self.actor)
        # TODO: check for ERR_NICKCOLLISION after server protocol is done

        if not self.actor.is_user():
            self.actor.user = self.user = User(to_nick)

        # Nickname collision
        if User.exists(to_nick):
            # Unless it's the same client sending its own nickname
            if self.user.registered.nick and\
               self.user.registered.user and\
               self.user is User.get(to_nick):
                return
            # TODO: KILL if not a local user
            return ERR_NICKNAMEINUSE(to_nick, self.actor)

        reg = self.user.registered

        if not reg.user and not reg.nick:
            self.user.nickname = to_nick
            self.user.registered.nick = True

        elif not reg.user and reg.nick:
            self.user.rename(to_nick)
            return M(self.actor, 'NICK', to_nick)

        elif reg.user and not reg.nick:
            self.user.nickname = to_nick
            self.user.registered.nick = True
            self.user.save()
            return welcome(self.actor) + [M(self.actor, 'NICK', to_nick)]
            #TODO: send NICK and USER to other servers

        elif reg.user and reg.nick:
            from_full = str(self.user)
            self.user.rename(to_nick)
            return M(ActorCollection([self.actor] + Server.all()),
                'NICK', to_nick, prefix=from_full)
