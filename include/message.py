from config import config
from . import abnf


class Error(Exception):
    pass


class Message(object):
    def __init__(self, target, command, *parameters, **kwargs):
        for parameter in parameters[:-1]:
            if ' ' in parameter:
                raise Error('Space can only appear in the very last parameter')
        self.command = command
        self.parameters = [x for x in parameters if x is not None]
        self.target = target
        self.prefix = str(kwargs['prefix']) if 'prefix' in kwargs else None
        self.add_nick = kwargs['add_nick'] if 'add_nick' in kwargs else False

    @staticmethod
    def from_string(string):
        if len(string) > 512:
            raise Error('Message must not be longer than 512 characters')
        raw = abnf.parse(string, abnf.message)
        if not raw:
            raise Error('Failed to parse message: ' + string)
        if config.get('parser', 'lowercase_commands'):
            raw[1] = raw[1].upper()
        msg = Message(None, prefix=raw.pop(0), *raw)
        return msg

    def __str__(self):
        params = self.parameters[:]
        for param in params[:-1]:
            if param is not None and ' ' in param:
                raise Error('Space can only appear in the very last parameter')
        if len(params) > 0 and ' ' in params[-1]:
            params[-1] = ':%s' % params[-1]
        return '{prefix}{command} {params}\r\n'.format(
            prefix=':%s ' % self.prefix if self.prefix is not None else '',
            command=str(self.command),
            params=' '.join(params)
        )

    def __repr__(self):
        return "'%s'" % str(self)[:-2]

    def __eq__(self, other):
        return isinstance(other, Message) \
        and self.prefix == other.prefix \
        and self.command == other.command \
        and self.parameters == other.parameters \
        and self.target == other.target
