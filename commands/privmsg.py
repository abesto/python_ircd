from typing import List

from commands.base import Command
from include.message import Message as M
from include.numeric_replies import *
from models import db, Actor, ActorCollection, Channel, User


class PrivmsgCommand(Command):
    required_parameter_count = 0
    command = "PRIVMSG"

    def from_user(self, receivers=None, text=None, *_):
        if receivers is None:
            return ERR_NORECIPIENT(self.command, self.actor)
        if text is None:
            return ERR_NOTEXTTOSEND(self.actor)
        resp = []
        # TODO: check for ERR_TOOMANYTARGETS
        for receiver in receivers.split(","):
            if db.exists(Channel, receiver):
                users = [
                    user
                    for user in db.get(Channel, receiver).users
                    if user is not self.user
                ]
                resp.append(
                    M(
                        ActorCollection(users),
                        self.command,
                        str(receiver),
                        text,
                        prefix=str(self.user),
                    )
                )
            elif db.exists(User, receiver):
                resp.append(
                    M(
                        db.get(User, receiver).actor,
                        self.command,
                        str(receiver),
                        text,
                        prefix=str(self.user),
                    )
                )
            # TODO: Implement wildcards
            # TODO: check for ERR_WILDTOPLEVEL, RPL_AWAY, ERR_NOTOPLEVEL
            else:
                resp.append(ERR_NOSUCHNICK(receiver, self.actor))
        return resp

    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")
