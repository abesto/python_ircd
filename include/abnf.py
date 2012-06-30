"""
Parse incoming messages using pyparsing.
Wildcards are recognized using regular expressions.
"""

from pyparsing import ParseException, oneOf, Suppress, Literal, Or, \
    ZeroOrMore, Group, Optional, OneOrMore, And, StringStart, StringEnd, Regex
from pydispatch import dispatcher

from config import config


def flatten(L):
    if not isinstance(L, list):
        return L
    ret = []
    for i in L:
        if isinstance(i, list):
            ret.extend(flatten(i))
        else:
            ret.append(i)
    return ret


def half_flatten(l):
    if all([type(x) is str for x in l]):
        return ''.join(l)
    return [half_flatten(x) for x in l]


def parse(str, parser):
    """ Public API"""
    try:
        return flatten(half_flatten(parser.parseString(str, True)))
    except ParseException:
        return False


def charclass(*classes):
    "Helper, similar to srange applied to [a-b]"
    l = []
    for (min, max) in classes:
        l += [chr(i) for i in range(min, max + 1)]
    return oneOf(l)

###
# Some core rules
###
alpha = charclass((0x41, 0x5A), (0x61, 0x7A))
digit = charclass((0x30, 0x39))
hexdigit = charclass((0x30, 0x39), (ord('A'), ord('F')))
space = Suppress(' ')
cr = Suppress('\r')
lf = Suppress('\n')
crlf = cr + lf

###
# IRC / python-ircd specific rules
###
soft_eol = cr ^ lf ^ crlf

letter = alpha
special = charclass((0x5B, 0x60), (0x7B, 0x7D))

nospcrlfcl = charclass(
    (0x01, 0x09),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x21, 0x39),
    (0x3B, 0xFF)
)

# Used as part of hostname
shortname = (letter ^ digit) + \
            ZeroOrMore(letter ^ digit ^ '-') + \
            ZeroOrMore(letter ^ digit)

hostname = shortname + ZeroOrMore('.' + shortname)

# Used as part of params
middle = Group(nospcrlfcl + ZeroOrMore(':' ^ nospcrlfcl))

# Used as part of params
trailing = Group(ZeroOrMore(oneOf([':', ' ']) ^ nospcrlfcl))

params = (((0, 14) * (space + middle)) +
             Optional(space + Suppress(':') + trailing)) ^ \
         (14 * (space + middle) +
          Optional(space + Optional(Suppress(':')) + trailing))
params.leaveWhitespace()

servername = hostname

ip4addr = 3 * ((1, 3) * digit + '.') + ((1, 3) * digit)
ip6addr = ('0:0:0:0:0:' + oneOf('0 FFFF') + ':' + ip4addr) ^ \
          (OneOrMore(hexdigit) + 7 * (':' + OneOrMore(hexdigit)))
hostaddr = ip4addr ^ ip6addr

host = hostname ^ hostaddr

user = OneOrMore(charclass(
    (0x01, 0x09),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x21, 0x3F),
    (0x41, 0xFF)
)).leaveWhitespace()


nickname = (letter ^ special) + \
           (0, 8) * (letter ^ digit ^ special ^ '-')

# Used as part of message
prefix = servername ^ \
         nickname + Optional('!' + user) + '@' + host

# Used as part of message
command = OneOrMore(letter) ^ (3 * digit)

message = None


def build_message():
    global message
    message = Group(Optional(Suppress(Literal(':')) + prefix + space)) + \
              Group(command) + \
              Group(Optional(params))
    if config.getboolean('parser', 'trailing_spaces'):
        message += ZeroOrMore(space)
    if config.getboolean('parser', 'soft_eol'):
        message += cr ^ lf ^ crlf
    else:
        message += crlf
    message.leaveWhitespace()
build_message()
dispatcher.connect(build_message, 'parser.trailing_spaces', 'config')
dispatcher.connect(build_message, 'parser.soft_eol', 'config')

chanstring = charclass(
    (0x01, 0x06),
    (0x08, 0x09),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x21, 0x2B),
    (0x2D, 0x39),
    (0x3B, 0xFF)
)
channelid = 5 * (charclass((0x41, 0x5A)) ^ digit)

channel = And([
    Or([
        oneOf('# + &'),
        Literal('!') + Group(channelid)
    ]),
    Group(OneOrMore(chanstring)),
    Optional(Suppress(Literal(':')) + Group(OneOrMore(chanstring)))
])

###
# Wildcard expressions
###
wildone = Literal('?')
wildmany = Literal('*')
nowild = charclass((0x01, 0x29), (0x2B, 0x3E), (0x40, 0xFF))
noesc = charclass((0x01, 0x5B), (0x5D, 0xFF))
mask = ZeroOrMore(nowild ^ (noesc + wildone) ^ (noesc + wildmany))

# Fall back to regex for parsing wildcards
matchone = '[%s-%s]' % (chr(0x01), chr(0xFF))
matchmany = '[%s-%s]*' % (chr(0x01), chr(0xFF))


def wild_to_match(char):
    if parse(char, wildone):
        return matchone
    if parse(char, wildmany):
        return matchmany
    return char


def wildcard(str):
    parsed = parse(str, mask)
    if not parsed:
        return parsed
    return StringStart() + \
           Regex(''.join([wild_to_match(x) for x in parsed])) + \
           StringEnd()
