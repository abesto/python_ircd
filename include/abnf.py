"""
Parse incoming messages using pyparsing.
Wildcards are recognized using regular expressions.
"""
from typing import List, Any, Optional as TOptional, Union, Tuple

from pyparsing import (
    ParseException,
    oneOf,
    Suppress,
    Literal,
    Or,
    ZeroOrMore,
    Group,
    Optional,
    OneOrMore,
    And,
    StringStart,
    StringEnd,
    Regex,
    ParserElement,
)

# pylint: disable=import-error
from pydispatch import dispatcher

# pylint: enable=import-error

from config import config


def flatten(data) -> List[Any]:
    """
    Flatten an arbitrarily deeply nested list of lists.
    Argument not typed pending recursive types, see https://github.com/python/mypy/issues/731
    """
    if not isinstance(data, list):
        return data
    ret = []
    for item in data:
        if isinstance(item, list):
            ret.extend(flatten(item))
        else:
            ret.append(item)
    return ret


def join_str_lists(data) -> Union[str, List[Any]]:
    """
    Traverse arbitrarily deeply nested lists. Any leaf lists containing
    only `str` instances get replaced with a concatenation of those strings.
    This transformation is _not_ propagated upwards (that would usually lead
    to the result being a single string, analogous to `''.join(flatten(data))`)

    Argument not typed pending recursive types, see https://github.com/python/mypy/issues/731
    """
    if all(isinstance(x, str) for x in data):
        return "".join(data)
    return [join_str_lists(x) for x in data]


def charclass(*classes: Tuple[int, int]) -> ParserElement:
    """Helper, similar to srange applied to [a-b]"""
    chars: List[str] = []
    for low, high in classes:
        chars += [chr(n) for n in range(low, high + 1)]
    return oneOf(chars)


class IrcParser:
    """
    pyparsing grammar for the subset of the IRC protocol supported by this project
    """

    ###
    # Some core rules
    ###
    alpha = charclass((0x41, 0x5A), (0x61, 0x7A))
    digit = charclass((0x30, 0x39))
    hexdigit = charclass((0x30, 0x39), (ord("A"), ord("F")))
    space = Suppress(" ")
    cr = Suppress("\r")
    lf = Suppress("\n")
    crlf = cr + lf

    ###
    # IRC / python-ircd specific rules
    ###
    soft_eol = cr ^ lf ^ crlf

    letter = alpha
    special = charclass((0x5B, 0x60), (0x7B, 0x7D))

    nospcrlfcl = charclass(
        (0x01, 0x09), (0x0B, 0x0C), (0x0E, 0x1F), (0x21, 0x39), (0x3B, 0xFF)
    )

    # Used as part of hostname
    shortname = (
        (letter ^ digit) + ZeroOrMore(letter ^ digit ^ "-") + ZeroOrMore(letter ^ digit)
    )

    hostname = shortname + ZeroOrMore("." + shortname)

    # Used as part of params
    middle = Group(nospcrlfcl + ZeroOrMore(":" ^ nospcrlfcl))

    # Used as part of params
    trailing = Group(ZeroOrMore(oneOf([":", " "]) ^ nospcrlfcl))

    params = (
        ((0, 14) * (space + middle)) + Optional(space + Suppress(":") + trailing)
    ) ^ (14 * (space + middle) + Optional(space + Optional(Suppress(":")) + trailing))
    params.leaveWhitespace()

    servername = hostname

    ip4addr = 3 * ((1, 3) * digit + ".") + ((1, 3) * digit)
    ip6addr = ("0:0:0:0:0:" + oneOf("0 FFFF") + ":" + ip4addr) ^ (
        OneOrMore(hexdigit) + 7 * (":" + OneOrMore(hexdigit))
    )
    hostaddr = ip4addr ^ ip6addr

    host = hostname ^ hostaddr

    user = OneOrMore(
        charclass((0x01, 0x09), (0x0B, 0x0C), (0x0E, 0x1F), (0x21, 0x3F), (0x41, 0xFF))
    ).leaveWhitespace()

    nickname = (letter ^ special) + (0, 8) * (letter ^ digit ^ special ^ "-")

    # Used as part of message
    prefix = servername ^ nickname + Optional("!" + user) + "@" + host

    # Used as part of message
    command = OneOrMore(letter) ^ (3 * digit)

    chanstring = charclass(
        (0x01, 0x06),
        (0x08, 0x09),
        (0x0B, 0x0C),
        (0x0E, 0x1F),
        (0x21, 0x2B),
        (0x2D, 0x39),
        (0x3B, 0xFF),
    )
    channelid = 5 * (charclass((0x41, 0x5A)) ^ digit)

    channel = And(
        [
            Or([oneOf("# + &"), Literal("!") + Group(channelid)]),
            Group(OneOrMore(chanstring)),
            Optional(Suppress(Literal(":")) + Group(OneOrMore(chanstring))),
        ]
    )

    ###
    # Wildcard expressions
    ###
    wildone = Literal("?")
    wildmany = Literal("*")
    nowild = charclass((0x01, 0x29), (0x2B, 0x3E), (0x40, 0xFF))
    noesc = charclass((0x01, 0x5B), (0x5D, 0xFF))
    mask = Optional(wildone ^ wildmany) + ZeroOrMore(
        nowild ^ (noesc + wildone) ^ (noesc + wildmany)
    )

    def __init__(self):
        self.message = None
        self.build_message()
        dispatcher.connect(self.build_message, "parser.trailing_spaces", "config")
        dispatcher.connect(self.build_message, "parser.soft_eol", "config")

    def build_message(self):
        """
        Generate the `message` subparser, taking into account configuration
        """
        self.message = (
            Group(Optional(Suppress(Literal(":")) + self.prefix + self.space))
            + Group(self.command)
            + Group(Optional(self.params))
        )
        if config.getboolean("parser", "trailing_spaces"):
            self.message += ZeroOrMore(self.space)
        if config.getboolean("parser", "soft_eol"):
            self.message += self.cr ^ self.lf ^ self.crlf
        else:
            self.message += self.crlf
        self.message.leaveWhitespace()

    # Fall back to regex for parsing wildcards
    matchone = "[%s-%s]" % (chr(0x01), chr(0xFF))
    matchmany = "[%s-%s]*" % (chr(0x01), chr(0xFF))

    @staticmethod
    def parse(input_str, parser) -> TOptional[List[Any]]:
        """Main entrypoint"""
        try:
            return flatten(join_str_lists(parser.parseString(input_str, True)))
        except ParseException:
            return None

    def wild_to_match(self, char) -> str:
        """Translate IRC wildcards to regex snippets"""
        if self.parse(char, self.wildone):
            return self.matchone
        if self.parse(char, self.wildmany):
            return self.matchmany
        return char

    def wildcard(self, input_str) -> ParserElement:
        """
        Generate a parser at runtime based on a user-supplied expression containing
        IRC wildcard characters
        """
        parsed = self.parse(input_str, self.mask)
        if parsed is None:
            raise Exception(
                'Failed to parse "{}" into a wildcard expression'.format(input_str)
            )
        return (
            StringStart()
            + Regex("".join(self.wild_to_match(x) for x in parsed))
            + StringEnd()
        )

    # Convenience methods to invoke individual parsers

    def parse_message(self, input_str):
        """Convenience method equivalent to parser.parse(input_str, parser.message)"""
        return self.parse(input_str, self.message)

    def parse_channel(self, input_str):
        """Convenience method equivalent to parser.parse(input_str, parser.channel)"""
        return self.parse(input_str, self.channel)

    def parse_nickname(self, input_str):
        """Convenience method equivalent to parser.parse(input_str, parser.nickname)"""
        return self.parse(input_str, self.nickname)


DEFAULT_PARSER = IrcParser()


def default_parser() -> IrcParser:
    """Used to access a global IrcParser instance (as opposed to DI)"""
    return DEFAULT_PARSER


__all__ = ["IrcParser", "default_parser"]
