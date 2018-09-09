from dns import resolver, reversename
from typing import List

from commands.base import Command
from include.message import Message
from include.numeric_replies import *
from models.user import User
from ._welcome import welcome


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

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
