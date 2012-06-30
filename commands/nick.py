from commands.base import Command
from models import User, Server
from message import Message as M
from numeric_responses import *
import abnf
from _welcome import welcome


class NickCommand(Command):
    required_parameter_count = 0
    command = 'NICK'
    must_be_registered = False

    def from_user(self, to_nick=None, hopcount=None):
        if to_nick is None:
            return ERR_NONICKNAMEGIVEN(self.actor)
        if len(to_nick) > 9 or abnf.parse(to_nick, abnf.nickname) != to_nick:
            return ERR_ERRONEUSNICKNAME(to_nick, self.actor)
        # TODO: check for ERR_NICKCOLLISION after server protocol is done

        if not self.actor.is_user():
            from_nick = None
            self.actor.user = self.user = User(to_nick)
        else:
            from_nick = self.user.nickname

        # Nickname collision
        if User.exists(to_nick):
            # Unless it's the same client sending its own nickname
            if self.user.registered.both and\
               self.user is User.get(to_nick):
                return
            # TODO: KILL if not a local user
            return ERR_NICKNAMEINUSE(to_nick, self.actor)

        # New login, no collision
        if from_nick is None:
            self.user.registered.nick = True
            self.user.nickname = to_nick
            if self.user.registered.both:
                self.user.save()
                return welcome(self.actor)
                #TODO: send NICK and USER to other servers

        # NICK before registration is complete,
        # likely because the originally requested nick was already used
        if not self.user.registered.nick:
            rename = M(self.actor, 'NICK', to_nick, prefix=from_nick)
            self.user.nickname = to_nick
            self.user.registered.nick = True
            # USER command has already been received, complete registration
            if self.user.registered.both:
                self.user.save()
                return welcome(self.actor) + [rename]
                #TODO: send NICK and USER to other servers
            return rename

        # User is registered, this is a normal rename
        if self.user.registered.both:
            from_full = self.user
            self.user.rename(to_nick)
            return M(ActorCollection([self.actor] + Server.all()),
                from_full, 'NICK', to_nick)
