from dns import resolver, reversename

from commands.base import Command
from numeric_responses import *
import db


class UserCommand(Command):
    required_parameter_count = 4
    command = 'USER'
    must_be_registered = False

    def from_client(self, username, hostname, servername, realname):
        if self.user is None:
            self.user = db.connected(None, self.socket)
        if self.user.registered.user:
            return ERR_ALREADYREGISTRED(self.user)

        self.user.username = username
        self.user.hostname = self.socket.getpeername()[0]
        try:
            addr = reversename.from_address(self.user.hostname)
            self.user.hostname = str(resolver.query(addr,"PTR")[0])
        except:
            pass
        self.user.servername = config.servername
        self.user.realname = realname

        self.user.registered.user = True

        if self.user.registered.nick:
            db.registered(self.user)
            # TODO: return the rest of the welcome messages
            return [
                RPL_WELCOME(self.user),
                RPL_YOURHOST(self.user),
                RPL_CREATED(self.user)
            ]

