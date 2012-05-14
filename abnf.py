# DSL for parsing ABNF and parsers for the IRC grammar

class Error(Exception): pass


class ParserData:
    def __init__(self, str):
        self.original = str
        self.str = str
        self.captured = []

    def shift(self, n):
        ret = self.str[:n]
        self.str = self.str[n:]
        return ret

def parse(str, parser, partial=False):
    """ Public API"""
    data = ParserData(str)
    parsed = parser(data)
    if not partial and len(data.str) > 0:
        return False
    if len(data.captured) > 0:
        return data.captured
    return parsed

class parser(object):
    """
    Base class of all parsers
    """
    def __init__(self, capture=False):
        self.capture = capture
    def _parse(self, data):
        raise NotImplementedError()
    def processed(self):
        if self.data.str == '':
            return self.checkpoint[0]
        return self.checkpoint[0][:-len(self.data.str)]
    def __call__(self, data):
        self.data = data
        self.checkpoint = (data.str, data.captured[0:])
        retval = self._parse(data)
        if not retval:
            (data.str, data.captured) = self.checkpoint
            retval = False
        if retval is True:
            retval = self.processed()
        if self.capture and retval:
            self.data.captured.append(retval)
        return retval

###
# Combinators
###
class either(parser):
    def __init__(self, *args, **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.rules = args
    def _parse(self, data):
        for f in self.rules:
            if f(data):
                return self.processed()
        return False
    def __str__(self):
        return '( ' + ' / '.join([str(r) for r in self.rules]) + ' )'

class repeat(parser):
    def __init__(self, rule, min=0, max=float('inf'), **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.rule = rule
        self.min = min
        self.max = max
    def _parse(self, data):
        i = 0
        while i < self.min and self.rule(data):
            i += 1
        if i < self.min:
            return False
        while i < self.max and self.rule(data):
            i += 1
        return i <= self.max
    def __str__(self):
        if self.min == 0 and self.max == 1:
            return '[ ' + str(self.rule) + ' ]'
        ret = ''
        if self.min == self.max:
            ret += str(self.min)
        else:
            if self.min > 0:
                ret += str(self.min)
            ret += '*'
            if self.max < float('inf'):
                ret += str(self.max)
        return ret + '( ' + str(self.rule) + ' )'

class maybe(repeat):
    def __init__(self, rule, **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.rule = rule
        self.min = 0
        self.max = 1

class sequence(parser):
    def __init__(self, *args, **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.rules = args
    def _parse(self, data):
        for f in self.rules:
            if f(data) is False:
                return False
        return True
    def __str__(self):
        return ' '.join([str(r) for r in self.rules])
###
# Grammar elements
###
class string(parser):
    def __init__(self, string, **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.string = string
    def _parse(self, data):
        return self.string == data.shift(len(self.string))
    def __str__(self):
        return '"%s"'%self.string

class charclass(parser):
    def __init__(self, min, max, **kwargs):
        parser.__init__(self, kwargs['capture'] if 'capture' in kwargs else False)
        self.min = min
        self.max = max
    def _parse(self, data):
        c = data.shift(1)
        if c == '':
            return False
        n = ord(c)
        return self.min <= n <= self.max
    def __str__(self):
        return '%%x%s-%s' % (self.min, self.max)

###
# IRC-specific parsers
###
letter = either(
    charclass(0x41, 0x5A),
    charclass(0x61, 0x7A)
)
nospcrlfcl = either(
    charclass(0x01, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x39),
    charclass(0x3B, 0xFF)
)
digit = charclass(0x30, 0x39)
space = string(' ')

shortname = sequence(
    either(letter, digit),
    repeat(
        either(letter, digit, string('-'))
    ),
    repeat(
        either(letter, digit)
    )
)
hostname = sequence(
    shortname,
    repeat(sequence(
        string('.'), shortname
    ))
)

middle = sequence(
    nospcrlfcl,
    repeat(either(string(':'), nospcrlfcl)),
    capture=True
)

trailing = repeat(either(
    string(':'), string(' '), nospcrlfcl
), capture=True)

params = either(
    sequence(
        repeat(sequence(space, middle), 14, 14),
        maybe(sequence(space, maybe(string(':')), trailing))
    ),
    sequence(
        repeat(sequence(space, middle), 0, 14),
        maybe(sequence(space, string(':'), trailing))
    )
)


####
# Old parsers from here; these are now non-functional,
# and will be rewritten to the above format
###

def message(data):
    if data.apply(str_prefix(':')):
        if not data.apply(prefix):
            return False
        ret['prefix'] = data.last
        if not data.apply(space):
            return False

    ret['command'] = data.apply(command)
    if not ret['command']:
        return False

    if data.apply(crlf):
        return ret

    ret['params'] = data.apply(params)

    if ret['params'] == False or not data.apply(crlf):
        return False

    return ret

def prefix(data):
    ret = data.apply(servername)
    if ret:
        return ret
    ret = {
        'nickname': data.apply(nickname),
        'user': None,
        'host': None
    }
    if not ret['nickname']:
        return False

    if not data.apply(str_prefix('!')):
        return ret

    ret['user'] = data.apply(user)
    if not ret['user']:
        return False

    if not data.apply(str_prefix('@')):
        return ret

    ret['host'] = data.apply(host)
    if not ret['host']:
        return False

    return ret

def command(data):
    if data.repeat(letter):
        return data.last
    elif not data.repeat(digit, 3, 3):
        return False
    return data.last

def space(data):
    if data.shift(1) == ' ':
        return ' '
    return False

def crlf(data):
    return data.shift(2) == '\r\n'

def userchar(data):
    return char_inrange(data,
        (0x01, 0x09),
        (0x0B, 0x0C),
        (0x0E, 0x1F),
        (0x21, 0x3F),
        (0x41, 0xFF)
    )
def user(data):
    return data.repeat(userchar, 1)

def letter(data):
    return char_inrange(data,
        (0x41, 0x5A),
        (0x61, 0x7A)
    )

def hexdigit(data):
    return data.either(
        digit,
        str_prefix('A'),
        str_prefix('B'),
        str_prefix('C'),
        str_prefix('D'),
        str_prefix('E'),
        str_prefix('F'),
    )

def special(data):
    return char_inrange(data,
        (0x5B, 0x60),
        (0x7B, 0x7D)
    )

def nickname(data):
    if not data.either(letter, special):
        return False
    nickname = data.last

    i = 0
    while i < 8 and data.either(letter, digit, special, str_prefix('-')):
        nickname += data.last

    return nickname

def channel(data):
    ret = {
        'prefix': None,
        'id': None,
        'name': None,
        'mask': None
    }
    if data.either(*[str_prefix(c) for c in ['#', '+', '&', '!']]):
        ret['prefix'] = data.last
    else:
        return False

    if ret['prefix'] == '!':
        if data.apply(channelid):
            ret['id'] = data.last
        else:
            return False

    if not data.repeat(chanstring, 1, 50):
        return False
    ret['name'] = data.last

    if data.apply(str_prefix(':')):
        if not data.repeat(chanstring):
            return False
        ret['mask'] = data.last

    return ret

def chanstring(data):
    return char_inrange(data,
        (0x01, 0x07),
        (0x08, 0x09),
        (0x0B, 0x0C),
        (0x0E, 0x1F),
        (0x21, 0x2B),
        (0x2D, 0x39),
        (0x3B, 0xFF)
    )

def channelid_char(data):
    return char_inrange(data,
        (0x41, 0x5A),  # A-Z
        (0x30, 0x39)   # 0-0
    )
def channelid(data):
    return data.repeat(channelid_char, 5, 5)


def servername(data):
    return hostname(data)

def host(data):
    return data.either(hostname, hostaddr)


def hostaddr(data):
    return data.either(ip4addr, ip6addr)

def ip4addr(data):
    ret = ''

    for i in range(4):
        if not data.repeat(digit, 1, 3):
            return False
        ret += data.last
        if i < 3:
            if not data.apply(str_prefix('.')):
                return False
            ret += '.'

    return ret

def ip6_real(data):
    if not data.repeat(hexdigit, 1):
        return False
    ret = data.last
    for i in range(7):
        if not data.apply(str_prefix(':')):
            return False
        ret += ':'
        if not data.repeat(hexdigit, 1):
            return False
        ret += data.last

def ip6_wrap(data):
    if not data.repeat(str_prefix('0:'),5):
        return False
    ret = data.last
    if not data.either(str_prefix('0:'), str_prefix('FFFF:')):
        return False
    ret += data.last
    if not data.apply(ip4addr):
        return False
    ret += data.last
    return ret

def ip6addr(data):
    return data.either(ip6_real, ip6_wrap)
