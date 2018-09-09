import itertools

import logging
from typing import List

log = logging.getLogger(__name__)

from config import config
from commands.quit import QuitCommand
from include.message import Message


class Error(Exception):
    pass


class Router(object):
    async def send(self, messages: List[Message]):
        if messages is None:
            return

        actors = set()

        for message in messages:
            # Default prefix is the servername
            if message.prefix is None:
                message.prefix = config.get("server", "servername")
            actors.add(message.target)
            message.target.write(message)
            log.debug("=> %s %s" % (repr(message.target), repr(message)))

        for target in actors:
            await target.flush()

        for actor in itertools.chain.from_iterable(actors):
            if actor.connection_dropped:
                if actor.is_user():
                    cmd = QuitCommand()
                    message = Message(actor, "QUIT", "Connection lost")
                    await self.send(cmd.handle(actor, message))
                # TODO: is_server

            if actor.disconnected:
                actor.connection.close()
