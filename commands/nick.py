from typing import List

from commands.base import Command
from models import Server
from models.user import User
from models.server import Server
from models.actorcollection import ActorCollection

from include import abnf
from include.numeric_responses import *
from include.message import Message as M

from ._welcome import welcome


class ReturnNone(object):
    pass


class Parameters(object):
    def __init__(self, nick, hopcount):
        self.nick = nick
        self.hopcount = hopcount

    def got_nick(self):
        return self.nick is not None


class NickCommand(Command):
    required_parameter_count = 0
    command = 'NICK'
    user_registration_command = True

    def __init__(self):
        super(NickCommand, self).__init__()
        self.build_handlers()
        self.build_checks()

    def from_user(self, to_nick=None, hopcount=None, *_):
        self.params = Parameters(to_nick, hopcount)
        self.initialize_user_if_new()
        checks_result = self.run_checks()
        if checks_result is ReturnNone:
            return None
        if checks_result is not None:
            return checks_result
        return self.run_handler()

    def initialize_user_if_new(self):
        if not self.actor.is_user():
            self.actor.user = self.user = User(self.params.nick)

    def build_checks(self):
        self.checks = [
            self.check_missing_nick, self.check_invalid_nick,
            self.check_network_nickcollision, self.check_local_nickcollision
        ]

    def run_checks(self):
        for check in self.checks:
            retval = check()
            if retval is not None:
                return retval

    def check_missing_nick(self):
        if not self.params.got_nick():
            return ERR_NONICKNAMEGIVEN(self.actor)

    def check_invalid_nick(self):
        parsed_nick = abnf.parse(self.params.nick, abnf.nickname)
        if len(self.params.nick) > 9 or parsed_nick != self.params.nick:
            nick = self.params.nick.replace(' ', '_')
            return ERR_ERRONEUSNICKNAME(nick, self.actor)

    def check_network_nickcollision(self):
        # TODO: check for ERR_NICKCOLLISION
        pass

    def check_local_nickcollision(self):
        # no such nick yet
        if not User.exists(self.params.nick):
            return
        # client sending its own nickname
        if self.user.registered.nick and\
           self.user.registered.user and\
           self.user is User.get(self.params.nick):
            return ReturnNone
        # real collision
        return ERR_NICKNAMEINUSE(self.params.nick, self.actor)

    def build_handlers(self):
        self.handlers = {
            False: {
                False: self.preuser_first,
                True: self.preuser_rename
            },
            True: {
                False: self.register,
                True: self.rename
            }
        }

    def run_handler(self):
        reg = self.user.registered
        return self.handlers[reg.user][reg.nick]()

    def preuser_first(self):
        self.user.nickname = self.params.nick
        self.user.registered.nick = True

    def preuser_rename(self):
        self.user.rename(self.params.nick)
        return M(self.actor, 'NICK', self.params.nick)

    def register(self):
        self.user.nickname = self.params.nick
        self.user.registered.nick = True
        self.user.save()
        return welcome(self.actor) + [M(self.actor, 'NICK', self.params.nick)]
        #TODO: send NICK and USER to other servers

    def rename(self):
        from_full = str(self.user)
        self.user.rename(self.params.nick)
        targets = [self.actor] + Server.all()
        for channel in self.user.channels:
            targets += channel.users
        return M(ActorCollection(targets),
                 'NICK', self.params.nick,
                 prefix=from_full)
