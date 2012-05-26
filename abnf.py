import config
from pyparsing import ParseException, oneOf, Suppress, Literal, Or, ZeroOrMore, Group, Optional, OneOrMore, And


def flatten(L):
    if not isinstance(L,list):
        return L
    ret = []
    for i in L:
        if isinstance(i,list):
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

# Helper; similar to srange applied to [a-b]
def charclass(a, b): return oneOf([chr(i) for i in range(a,b+1)])

###
# Some core rules
###
alpha = charclass(0x41, 0x5A) ^ charclass(0x61, 0x7A)
digit = charclass(0x30, 0x39)
hexdigit = digit ^ oneOf('A B C D E F')
space = Suppress(Literal(' '))
cr = Suppress(Literal('\r'))
lf = Suppress(Literal('\n'))
crlf = cr + lf

###
# IRC / python-ircd specific rules
###
soft_eol = cr ^ lf ^ crlf

letter = alpha
special = charclass(0x5B, 0x60) ^ charclass(0x7B, 0x7D)

nospcrlfcl = Or([
    charclass(0x01, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x39),
    charclass(0x3B, 0xFF)
])

# Used as part of hostname
shortname = (letter ^ digit) + \
            ZeroOrMore(letter ^ digit ^ Literal('-')) + \
            ZeroOrMore(letter ^ digit)

hostname = shortname + ZeroOrMore(Literal('.') + shortname)

# Used as part of params
middle = Group(nospcrlfcl + ZeroOrMore(Literal(':') ^ nospcrlfcl))

# Used as part of params
trailing = Group(ZeroOrMore(oneOf([':', ' ']) ^ nospcrlfcl))

params = (((0,14)*(space + middle)) + Optional(space + Suppress(Literal(':')) + trailing)) ^ \
         (14*(space + middle) + Optional(space + Optional(Suppress(Literal(':'))) + trailing))
params.leaveWhitespace()

servername = hostname

ip4addr = 3*((1,3)*digit + Literal('.')) + ((1,3)*digit)
ip6addr = (Literal('0:0:0:0:0:') + oneOf('0 FFFF') + Literal(':') + ip4addr) ^ \
          (OneOrMore(hexdigit) + 7*(Literal(':') + OneOrMore(hexdigit)))
hostaddr = ip4addr ^ ip6addr

host = hostname ^ hostaddr

user = OneOrMore(Or([
    charclass(0x01, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x3F),
    charclass(0x41, 0xFF)
])).leaveWhitespace()


nickname = (letter ^ special) + (0,8)*(letter ^ digit ^ special ^ Literal('-'))

# Used as part of message
prefix = servername ^ \
         nickname + Optional(Literal('!') + user) + Literal('@') + host

# Used as part of message
command = OneOrMore(letter) ^ 3*digit

message = Group(Optional(Literal(':') + prefix + space)) + \
          Group(command) + \
          Group(Optional(params))
if config.traling_spaces:
    message += ZeroOrMore(space)
if config.soft_eol:
    message += cr ^ lf ^ crlf
else:
    message += crlf
message.leaveWhitespace()

chanstring = Or([
    charclass(0x01, 0x06),
    charclass(0x08, 0x09),
    charclass(0x0B, 0x0C),
    charclass(0x0E, 0x1F),
    charclass(0x21, 0x2B),
    charclass(0x2D, 0x39),
    charclass(0x3B, 0xFF)
])
channelid = 5*(charclass(0x41, 0x5A) ^ digit)

channel = And([
    Or([
        oneOf('# + &'),
        Literal('!') + Group(channelid)
    ]),
    Group(OneOrMore(chanstring)),
    Optional(Suppress(Literal(':')) + Group(OneOrMore(chanstring)))
])

