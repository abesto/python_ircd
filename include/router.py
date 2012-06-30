import logging
import itertools


log = logging.getLogger(__name__)

from config import config


class Error(Exception):
    pass


class Router(object):
    def __init__(self, shutdown_signal):
        self.shutdown_signal = shutdown_signal

    def send(self, messages):
        if messages is None:
            return

        if not isinstance(messages, list):
            messages = [messages]

        actors = set()

        for message in messages:
            # Default prefix is the servername
            if message.prefix is None:
                message.prefix = config.get('server', 'servername')
            actors.add(message.target)
            message.target.write(message)
            log.debug('=> %s %s' % (repr(message.target), repr(message)))

        for target in actors:
            target.flush()

        for actor in itertools.chain.from_iterable(actors):
            if actor.disconnected:
                try:
                    actor.socket.shutdown(self.shutdown_signal)
                except:
                    pass
                actor.socket.close()

