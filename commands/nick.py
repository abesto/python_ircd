from commands.base import Command
from db.models import User
from message import Message as M
from numeric_responses import *
import abnf
from _welcome import welcome


class NickCommand(Command):
    required_parameter_count = 0
    command = 'NICK'
    must_be_registered = False

    def from_client(self, to_nick=None, hopcount=None):
        if to_nick is None:
            return ERR_NONICKNAMEGIVEN(User(None, self.socket))
        if len(to_nick) > 9 or abnf.parse(to_nick, abnf.nickname) != to_nick:
            return ERR_ERRONEUSNICKNAME(
                to_nick,
                User(None, self.socket))
        # TODO: check for ERR_NICKCOLLISION after server protocol is done

        if self.user is None:
            from_nick = None
            self.user = self.db.connected(to_nick, self.socket)
        else:
            from_nick = self.user.nickname

        # Nickname collision
        if self.db.user_exists(to_nick):
            # Unless it's the same client sending its own nickname
            if self.user.registered.both and\
               self.user is self.db.get_user(to_nick):
                return
            # TODO: KILL if not a local user
            return ERR_NICKNAMEINUSE(to_nick, self.user)

        # New login, no collision
        if from_nick is None:
            self.user.registered.nick = True
            self.user.nickname = to_nick
            if self.user.registered.both:
                self.db.registered(self.user)
                # TODO: rest of the welcome messages
                return welcome(self.user)
                #TODO: send NICK and USER to other servers

        # NICK before registration is complete,
        # likely because the originally requested nick was already used
        if not self.user.registered.nick:
            rename = M(self.user, 'NICK', to_nick, prefix=from_nick)
            self.user.nickname = to_nick
            self.user.registered.nick = True
            # USER command has already been received, complete registration
            if self.user.registered.both:
                self.db.registered(self.user)
                # TODO: rest of the welcome messages
                return welcome(self.user) + [rename]
                #TODO: send NICK and USER to other servers
            return rename

        # User is registered, this is a normal rename
        if self.user.registered.both:
            from_full = self.user
            self.db.rename(from_nick, to_nick)
            return M(
                [self.user] + self.db.all_servers(),
                from_full, 'NICK', to_nick)
