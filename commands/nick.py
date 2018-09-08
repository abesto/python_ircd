"""
`NickCommand`: Implements the NICK IRC command
"""
import logging
from typing import List, NamedTuple, Callable, Dict

from commands.base import Command
from include import abnf
from include.message import Message
from include.numeric_responses import (
    ERR_NONICKNAMEGIVEN,
    ERR_ERRONEUSNICKNAME,
    ERR_NICKNAMEINUSE,
)
from models.actorcollection import ActorCollection
from models.server import Server
from models.user import User, RegistrationStatus
from ._welcome import welcome

__all__ = ["NickCommand"]


LOG = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class CheckResult(NamedTuple):
    """Represents results of checking the parameters of a NICK command"""

    requested_and_current_nick_are_the_same: bool = False
    errors: List[Message] = []


class Parameters:
    """
    Encapsulates logic for parsing arguments specific to NICK

    Parameters: <nickname> [ <hopcount> ]
    """

    def __init__(self, nick, hopcount):
        self.nick = nick
        self.hopcount = None
        if hopcount is not None:
            try:
                self.hopcount = int(hopcount)
            except ValueError:
                LOG.warning("NICK command received non-numeric hopcount: %s", hopcount)

    def got_nick(self) -> bool:
        """Check whether a nickname was received"""
        return self.nick is not None

    def got_hopcount(self) -> bool:
        """Check whether a valid hopcount was received"""
        return self.hopcount is not None


class NickCommand(Command):
    """
    Implements the NICK IRC command
    https://tools.ietf.org/html/rfc1459#section-4.1.2
    """

    required_parameter_count = 0
    command = "NICK"
    user_registration_command = True

    def __init__(self):
        super(NickCommand, self).__init__()
        self.params: Parameters = None
        self.checks: List[Callable[[], CheckResult]] = self.build_checks()
        self.handlers: Dict[
            RegistrationStatus, Callable[[], List[Message]]
        ] = self.build_handlers()

    def from_server(self, *args):
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")

    # pylint: disable=arguments-differ,keyword-arg-before-vararg
    def from_user(self, to_nick=None, hopcount=None, *_) -> List[Message]:
        """
        Sets the nickname of the calling user to `to_nick`, except if
          * they already have the nick, in which case nothing happens
          * the target nickname is not specified, or is invalid, both resulting in errors
          * the nickname is already taken, in which case we return an error
        """
        self.params = Parameters(to_nick, hopcount)
        self.initialize_user_if_new()
        checks_result = self.run_checks()
        if checks_result.requested_and_current_nick_are_the_same:
            return []
        if checks_result.errors:
            return checks_result.errors
        return self.run_handler()

    # pylint: enable=arguments-differ,keyword-arg-before-vararg

    def initialize_user_if_new(self):
        """
        If the NICK command was issued by a user, and we don't yet have
        a relevant `User` object attached to the `Actor` representing them,
        create the object and attach it.
        """
        if not self.actor.is_user():
            self.actor.user = self.user = User(self.params.nick)

    def build_checks(self) -> List[Callable[[], CheckResult]]:
        """Specify the list of checks that'll be run to validate the command"""
        return [
            self.check_missing_nick,
            self.check_invalid_nick,
            self.check_network_nickcollision,
            self.check_local_nickcollision,
        ]

    def run_checks(self) -> CheckResult:
        """Run checks to validate the NICK command"""
        for check in self.checks:
            retval = check()
            if retval.errors or retval.requested_and_current_nick_are_the_same:
                return retval
        return CheckResult()

    def check_missing_nick(self) -> CheckResult:
        """Verify that we received a nickname"""
        if not self.params.got_nick():
            return CheckResult(errors=[ERR_NONICKNAMEGIVEN(self.actor)])
        return CheckResult()

    def check_invalid_nick(self) -> CheckResult:
        """Verify that the nickname we received is valid"""
        parsed_nick = abnf.default_parser().parse_nickname(self.params.nick)
        if len(self.params.nick) > 9 or parsed_nick != self.params.nick:
            nick = self.params.nick.replace(" ", "_")
            return CheckResult(errors=[ERR_ERRONEUSNICKNAME(nick, self.actor)])
        return CheckResult()

    # pylint: disable=no-self-use
    def check_network_nickcollision(self):
        """Verify there's no nick collision anywhere on the IRC network"""
        # TODO: check for ERR_NICKCOLLISION
        return CheckResult()

    # pylint: enable=no-self-use

    def check_local_nickcollision(self):
        """Verify there's no nick collision on this server"""
        # no such nick yet
        if not User.exists(self.params.nick):
            return CheckResult()
        # client sending its own nickname
        if (
            self.user.registered.nick
            and self.user.registered.user
            and self.user is User.get(self.params.nick)
        ):
            return CheckResult(requested_and_current_nick_are_the_same=True)
        # real collision
        return CheckResult(errors=[ERR_NICKNAMEINUSE(self.params.nick, self.actor)])

    def build_handlers(self) -> Dict[RegistrationStatus, Callable[[], List[Message]]]:
        """
        Metaprogramming: decide what to do based on the registration status of the user
        """
        return {
            RegistrationStatus(nick=False, user=False): self.preuser_first,
            RegistrationStatus(nick=False, user=True): self.register,
            RegistrationStatus(nick=True, user=False): self.preuser_rename,
            RegistrationStatus(nick=True, user=True): self.rename,
        }

    def run_handler(self) -> List[Message]:
        """Execute the right handler, with the handler map built in `build_handlers`"""
        return self.handlers[self.user.registered]()

    def preuser_first(self):
        """NICK command received before USER command; bookkeeping only"""
        self.user.nickname = self.params.nick
        self.user.registered.nick = True

    def preuser_rename(self) -> List[Message]:
        """
        A non-first NICK command received before any USER command.
        ACK the command to the user, but no other action is taken.
        """
        self.user.rename(self.params.nick)
        return [Message(self.actor, "NICK", self.params.nick)]

    def register(self) -> List[Message]:
        """First NICK command after USER, completing registration, and triggering MOTD"""
        self.user.nickname = self.params.nick
        self.user.registered.nick = True
        self.user.save()
        return welcome(self.actor) + [Message(self.actor, "NICK", self.params.nick)]
        # TODO: send NICK and USER to other servers

    def rename(self) -> List[Message]:
        """Renaming a registered user"""
        from_full = str(self.user)
        self.user.rename(self.params.nick)
        targets = [self.actor] + Server.all()
        for channel in self.user.channels:
            targets += channel.users
        return [
            Message(
                ActorCollection(targets), "NICK", self.params.nick, prefix=from_full
            )
        ]
