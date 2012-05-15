"""
A DSL for building ABNF parsers, and IRC-specific parsers
"""

import config


class Error(Exception): pass


class ParserData:
    def __init__(self, str):
        self.original = str
        self.str = str
        self.captures = []
        self.named_captures = {}

    def shift(self, n):
        ret = self.str[:n]
        self.str = self.str[n:]
        return ret


class ParseResult:
    def __init__(self, data):
        self.parsed = data.original[:-len(data.str)] if len(data.str) > 0 else data.original
        self.captures = data.captures
        self.named_captures = data.named_captures
    def __getitem__(self, item):
        if self.parsed is False:
            return None
        if type(item) is int:
            return self.captures[item]
        return self.named_captures[item]
    def has_key(self, key):
        if self.parsed is False:
            return False
        return self.named_captures.has_key(key)


def parse(str, parser, partial=False):
    """ Public API"""
    data = ParserData(str)
    retval = parser(data)
    result = ParseResult(data)
    if not retval or (not partial and len(data.str) > 0):
        result.parsed = False
        result.captures = False
        result.named_captures = False
    return result


class parser(object):
    """
    Base class of all parsers
    """
    def _parse(self, data):
        raise NotImplementedError()
    def processed(self):
        if self.data.str == '':
            return self.checkpoint[0]
        return self.checkpoint[0][:-len(self.data.str)]
    def __call__(self, data):
        self.data = data
        self.checkpoint = (data.str, data.captures[0:])
        retval = self._parse(data)
        if not retval:
            (data.str, data.captures) = self.checkpoint
            retval = False
        if retval is True:
            retval = self.processed()
        return retval

###
# ABNF operators
###
class sequence(parser):
    """
    Sequence group

    Example: map_sector = sequence(digit, letter)
    """
    def __init__(self, *args):
        parser.__init__(self)
        self.rules = list(args)
    def _parse(self, data):
        for f in self.rules:
            if f(data) is False:
                return False
        return True
    def __str__(self):
        return ' '.join([str(r) for r in self.rules])

class either(parser):
    """
    Alternatives

    Note that the alternatives are tried in the order given to the constructor.
    This means that the longest / least strict alternative should come first
    (for appropriate values of "strict").

    Example: alphanum = either(letter, digit)
    """
    def __init__(self, *args):
        parser.__init__(self)
        self.rules = list(args)
    def _parse(self, data):
        for f in self.rules:
            if f(data):
                return self.processed()
        return False
    def __str__(self):
        return '( ' + ' / '.join([str(r) for r in self.rules]) + ' )'

class charclass(parser):
    """
    Value range

    The constructor takes two integers: the min and the max values. Any
    character with a character code as defined by `ord` between min and max
    inclusive will be matched.

    Example: lowercase = charclass(ord('a'), ord('z'))
    """
    def __init__(self, min, max):
        parser.__init__(self)
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

class repeat(parser):
    """
    Variable repetition

    Applies `rule` at least `min`, at most `max` times. The default is to
    apply it as many times as possible, but never fail (min=0, max=infinity)

    Example: ip4_part = repeat(digit, 1, 3)

    Specific repetition: if min == max, this acts and prints as specific repetition
    Optional rule: if min == 0 and max == 1, this acts and prints as
                   a single rule within an optional sequence
    """
    def __init__(self, rule, min=0, max=float('inf')):
        parser.__init__(self)
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


def maybe(*args):
    """
    Optional sequence
    """
    return repeat(sequence(*args), 0, 1)


###
# Terminals
###
class string(parser):
    """
    A sequence of values given as a Python string
    """
    def __init__(self, string):
        parser.__init__(self)
        self.string = string
    def _parse(self, data):
        return self.string == data.shift(len(self.string))
    def __str__(self):
        return '"%s"'%self.string

###
# Helpers
###
class capture(sequence):
    """
    Capture sequence

    Works the same as a sequence, but the matched string gets added to the
    list of matched substrings
    """
    def __init__(self, *args, **kwargs):
        sequence.__init__(self, *args)
        self.name = kwargs['name'] if kwargs.has_key('name') else None
    def __call__(self, data):
        retval = sequence.__call__(self, data)
        if retval:
            if self.name is None:
                self.data.captures.append(retval)
            else:
                self.data.named_captures[self.name] = retval
        return retval

###
# Some core rules
###
alpha = either(
    charclass(0x41, 0x5A),  # a-z
    charclass(0x61, 0x7A)   # A-Z
)
digit = charclass(0x30, 0x39)
hexdigit = either(
    digit,
    string('A'),
    string('B'),
    string('C'),
    string('D'),
    string('E'),
    string('F'),
)
space = string(' ')
cr = string('\r')
lf = string('\n')
crlf = sequence(cr, lf)

###
# IRC / python-ircd specific rules
###
soft_eol = either(
    cr,
    lf,
    sequence(cr, lf)
)

letter = alpha
special = either(
    charclass(0x5B, 0x60),
    charclass(0x7B, 0x7D)
)

nospcrlfcl = either(
    charclass(0x01, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x39),
    charclass(0x3B, 0xFF)
)

# Used as part of hostname
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

# Used as part of params
middle = sequence(
    nospcrlfcl,
    repeat(either(string(':'), nospcrlfcl))
)

# Used as part of params
trailing = repeat(either(
    string(':'), string(' '), nospcrlfcl
))

params = either(
    sequence(
        repeat(sequence(space, capture(middle)), 14, 14),
        maybe(sequence(space, maybe(string(':')), capture(trailing)))
    ),
    sequence(
        repeat(sequence(space, capture(middle)), 0, 14),
        maybe(sequence(space, string(':'), capture(trailing)))
    )
)

servername = hostname

ip4addr = sequence(
    repeat(digit, 1, 3),
    string('.'),
    repeat(digit, 1, 3),
    string('.'),
    repeat(digit, 1, 3),
    string('.'),
    repeat(digit, 1, 3)
)
ip6addr = either(
    sequence(
        string('0:0:0:0:0:'),
        either(string('0'), string('FFFF')),
        string(':'),
        ip4addr
    ),
    sequence(
        repeat(hexdigit, 1),
        repeat(
            sequence(string(':'), repeat(hexdigit, 1)),
            7, 7
        )
    )
)
hostaddr = either(ip4addr, ip6addr)

host = either(hostname, hostaddr)

user = repeat(
    either(
        charclass(0x01, 0x09),
        charclass(0x0B, 0x0C),
        charclass(0x0E, 0x1F),
        charclass(0x21, 0x3F),
        charclass(0x41, 0xFF)
    ), 1 # to infinity
)

nickname = sequence(
    either(letter, special),
    repeat(either(letter, digit, special, string('-')), 0, 8)
)

# Used as part of message
prefix = either(
    servername,
    sequence(nickname,
        maybe(
            maybe(string('!'), user),
            string('@'),
            host
        )
    )
)

# Used as part of message
command = either(
    repeat(letter, 1),
    repeat(digit, 3, 3)
)

message = sequence(
    maybe(string(':'), capture(prefix, name='prefix'), space),
    capture(command, name='command'),
    maybe(params),
    crlf
)

chanstring = either(
    charclass(0x01, 0x07),
    charclass(0x08, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x2B),
    charclass(0x2D, 0x39),
    charclass(0x3B, 0xFF)
)
channelid = repeat(
    either(
        charclass(0x41, 0x5A),
        digit
    ), 5, 5
)

channel = sequence(
    either(
        string('#'),
        string('+'),
        sequence(string('!'), channelid),
        string('&')
    ),
    chanstring,
    maybe(string(':'), chanstring)
)


###
# Make parsing less picky based on enabled config options
###
if config.traling_spaces:
    message.rules.insert(-1, repeat(space))
if config.soft_eol:
    message.rules[-1] = soft_eol
