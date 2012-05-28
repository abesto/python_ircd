import logging
log = logging.getLogger(__name__)

from config import config
from db.models import User


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
        # Unify into a list of targets
        if not isinstance(message.target, type([])):
            message.target = [message.target]
        for target in message.target:
            # If we're sending this to a user,
            # add their nick as the first parameter
            if message.add_nick and isinstance(target, User):
                message.parameters.insert(0, target.nickname)
            targets.add(target)
            target.write(message)
            log.debug('=> %s %s' % (repr(target), repr(message)))
            # And remove the nick after we've sent the message
            if message.add_nick and isinstance(target, User):
                message.parameters = message.parameters[1:]
    for target in targets:
        target.flush()
