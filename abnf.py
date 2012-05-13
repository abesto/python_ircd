# Parsers for the ABNF definitions of RFC2812 Section 2.3.1
# This is _not_ a generic ABNF parser, just some helper functions
# and explicit parsing of the grammar specified in the RFC
# without the use of regular expressions

class Error(Exception): pass


class ParserData:
    """
    State data used by the parser functions
    """
    def __init__(self, str):
        self.stack = []
        self.original = str
        self.str = str
        self.last = ''

    def shift(self, n):
        self.stack.append(self.str[:n])
        self.str = self.str[n:]
        return self.stack[-1]

    def apply(self, f):
        before = self.str
        retval = f(self)
        if not retval:
            self.str = before
            return False
        self.last = retval
        return retval

    def either(self, *args):
        for f in args:
            retval = self.apply(f)
            if retval:
                self.last = retval
                return retval
        return False

    def repeat(self, f, min=0, max=float('inf'), initial=''):
        ret = initial
        i = 0
        while i < min and self.apply(f):
            ret += self.last
            i += 1
        if i < min:
            return False
        while i < max and self.apply(f):
            ret += self.last
        self.last = ret
        return ret


def parse(str, parser, partial=False):
    data = ParserData(str)
    parsed = parser(data)
    if not partial and len(data.str) > 0:
        return False
    return parsed



###
# Parser functions
###

def message(data):
    ret = {
        'prefix': None,
        'command': '',
        'params': []
    }
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

def params(data):
    ret = []
    for i in range(14):
        if not data.apply(str_prefix(' ')):
            return ret
        param = data.apply(middle)

        # trailing before 14 middles
        if not param:
            if not data.apply(str_prefix(':')):
                return False
            param = data.apply(trailing)
            if not param:
                return False
            ret.append(param)
            return ret

        # no trailing
        ret.append(param)

    # trailing after 14 middles
    if data.apply(str_prefix(' ')):
        data.apply(str_prefix(':'))
        param = data.apply(trailing)
        if not param:
            return False
        ret.append(param)

    return ret

def char_inrange(data, *args):
    c = data.shift(1)
    if c == '':
        return False
    n = ord(c)
    for tuple in args:
        if tuple[0] <= n <= tuple[1]:
            return c
    return False

def nospcrlfcl(data):
    return char_inrange(data,
        (0x01, 0x09),
        (0x0B, 0x0C),
        (0x0E, 0x1F),
        (0x21, 0x39),
        (0x3B, 0xFF)
    )

def middle(data):
    ret = data.apply(nospcrlfcl)
    if not ret:
        return False
    while data.either(str_prefix(':'), nospcrlfcl):
        ret += data.last
    return ret

def trailing(data):
    ret = ''
    while data.either(str_prefix(':'), str_prefix(' '), nospcrlfcl):
        ret += data.last
    if ret == '':
        return False
    return ret

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

def digit(data):
    return char_inrange(data, (0x30, 0x39))

def str_prefix(str):
    return lambda data: str if data.shift(len(str)) == str else False

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

def hostname(data):
    ret = data.apply(shortname)
    if not ret:
        return False
    while data.apply(str_prefix('.')):
        sn = data.apply(shortname)
        if not sn:
            return False
        ret += '.' + sn
    return ret

def shortname(data):
    if not data.either(letter, digit):
        return False
    ret = data.last
    while data.either(letter, digit, str_prefix('-')):
        ret += data.last
    if ret[-1] == '-':
        return False
    return ret

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
