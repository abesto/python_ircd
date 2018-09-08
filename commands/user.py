from dns import resolver, reversename

from config import config

from models.user import User
from include.numeric_responses import *

from ._welcome import welcome
from commands.base import Command


class UserCommand(Command):
    required_parameter_count = 4
    command = "USER"
    user_registration_command = True

    def from_user(self, username, hostname, servername, realname, *_):
        if not self.actor.is_user():
            self.actor.user = self.user = User(None)

        if self.user.registered.user:
            return ERR_ALREADYREGISTRED(self.actor)

        self.user.username = username
        self.user.hostname = self.actor.connection.get_peername()[0]
        try:
            addr = reversename.from_address(self.user.hostname)
            self.user.hostname = str(resolver.query(addr, "PTR")[0])
        except:
            pass
        self.user.servername = config.get("server", "servername")
        self.user.realname = realname

        self.user.registered.user = True

        if self.user.registered.nick:
            self.user.save()
            return welcome(self.actor)
