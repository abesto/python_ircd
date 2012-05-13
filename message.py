import abnf


class Error(Exception): pass


class Message(object):
    def __init__(self, target=None, prefix=None, command=None, *parameters):
        self.prefix = prefix
        self.command = command
        self.parameters = parameters
        self.target = target

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
        if self.target is not None:
            ret += ' -> %s' % self.target
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
    if not raw:
        raise Error('Failed to parse message: ' + str)
    return Message(None, raw['prefix'], raw['command'], *raw['params'])

