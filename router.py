import config


class Error(Exception): pass


def send(message):
    if message is None:
        return

    if not isinstance(message, type([])):
        messages = [message]
    else:
        messages = message

    targets = set()
    for message in messages:
        if message.prefix is None:
            message.prefix = config.servername
        if isinstance(message.target, type([])):
            for t in message.target:
                targets.add(t)
                t.write(message)
        else:
            targets.add(message.target)
            message.target.write(message)
    for target in targets:
        target.flush()

