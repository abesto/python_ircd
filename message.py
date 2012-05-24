import config
import abnf


class Error(Exception): pass


class Message(object):
    def __init__(self, target, command, *parameters, **kwargs):
        self.prefix = kwargs['prefix'] if kwargs.has_key('prefix') else None
        self.command = command
        self.parameters = filter(lambda x: x is not None, list(parameters))
        self.target = target
        self.add_nick = kwargs['add_nick'] if kwargs.has_key('add_nick') else False

    def __str__(self):
        ret = ''
        if self.prefix is not None:
            ret += ':%s ' % self.prefix
        ret += self.command
        for param in self.parameters[:-1]:
            if param is not None and ' ' in param:
                raise Error('Space can only appear in the very last parameter')
            ret += ' %s' % param
        if len(self.parameters) > 0:
            ret += ' '
            if ' ' in self.parameters[-1]:
                ret += ':'
            ret += self.parameters[-1]
        return ret + '\r\n'

    def __repr__(self):
        ret = "'" + str(self)[:-2] + "'"
        return ret

    def __eq__(self, other):
        return isinstance(other, Message) \
        and self.prefix == other.prefix \
        and self.command == other.command \
        and self.parameters == other.parameters \
        and self.target is other.target


def from_string(str):
    """
    @type str string
    """
    if len(str) > 512:
        raise Error('Message must not be longer than 512 characters')
    raw = abnf.parse(str, abnf.message)
    if not raw.parsed:
        raise Error('Failed to parse message: ' + str)
    msg = Message(
        None,
        raw['command'].upper() if config.lowercase_commands else raw['command'],
        *raw
    )
    if raw.has_key('prefix'):
        msg.prefix = raw['prefix']
    return msg

