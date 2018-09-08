import logging
import itertools


log = logging.getLogger(__name__)

from config import config
from commands.quit import QuitCommand
from include.message import Message as M


class Error(Exception):
    pass


class Router(object):
    async def send(self, messages):
        if messages is None:
            return

        if not isinstance(messages, list):
            messages = [messages]

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
                    message = M(None, "QUIT", "Connection lost")
                    await self.send(cmd.handle(actor, message))
                # TODO: is_server

            if actor.disconnected:
                actor.connection.close()
