import logging
log = logging.getLogger(__name__)

from config import config


class Error(Exception):
    pass


def send(message):
    if message is None:
        return

    # Unify into a list of messages
    if not isinstance(message, type([])):
        messages = [message]
    else:
        messages = message

    targets = set()  # The sockets we'll call flush on after everything is sent

    for message in messages:
        # Default prefix is the servername
        if message.prefix is None:
            message.prefix = config.get('server', 'servername')
        targets.add(message.target)
        message.target.write(message)
        log.debug('=> %s %s' % (repr(message.target), repr(message)))
    for target in targets:
        target.flush()
