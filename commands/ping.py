"""
`PingCommand`: Implements the PING IRC command
"""
from typing import List

from commands.base import Command
from include.message import Message


class PingCommand(Command):
    """Implements the PING IRC command"""
    def from_server(self, *args) -> List[Message]:
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")

    required_parameter_count = 1
    command = "PING"

    def from_user(self, *args):
        return Message(self.actor, "PONG", *args)
