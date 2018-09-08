"""
`Command`: Base class for classes representing individual IRC commands
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List

from include.message import Message
from include.numeric_responses import ERR_NOTREGISTERED, ERR_NEEDMOREPARAMS
from models import Actor

TMessage = TypeVar("TMessage", bound=Message)


class Command(Generic[TMessage], ABC):
    """
    Base class for classes representing individual IRC commands.

    The entry point is `handle`, which verifies the correctness of parameters, and uses
    `from_server`, `from_user`, and `common` to execute the command in question. A single
    instance can handle any number of sequential invocations.
    """

    @property
    @abstractmethod
    def required_parameter_count(self) -> int:
        """
        Number of required parameters for this command.
        `handle` returns `ERR_NEEDMOREPARAMS` is raised if not enough parameters are supplied.
        """
        pass

    @property
    @abstractmethod
    def command(self) -> str:
        """
        String representation of the IRC command this `Command` is prepared to handle.
        `handle` raises an exception if a `Message` with a different command is passed in.
        """
        pass

    user_registration_command: bool = False
    server_registration_command = False

    def __init__(self):
        self.message = None
        self.actor = None
        self.user = None
        self.server = None

    def cleanup(self):
        """Resets internal state between each execution"""
        self.message = None
        self.actor = None
        self.user = None
        self.server = None

    @abstractmethod
    def from_server(self, *args) -> List[Message]:
        """Execute this command, when sent by another IRC server"""
        pass

    @abstractmethod
    def from_user(self, *args) -> List[Message]:
        """Execute this command, when sent by a user"""
        pass

    # pylint: disable=no-self-use
    def common(self, *_) -> List[Message]:
        """Special logic during actor registration, shared by both user and server clients"""
        raise Exception(
            "`common` called on a `Command` subclass that was not expecting it"
        )

    def handle(self, actor: Actor, message: TMessage):
        """Execute this command, with parameters defined in the `message` sent by `actor`"""
        self.cleanup()
        self.actor = actor
        self.message = message

        if self.command != message.command:
            raise Exception("Wrong handler for " + repr(message))

        if not actor.is_user() and not actor.is_server():
            return self._handle_registration(actor, message)
        if len(message.parameters) < self.required_parameter_count:
            return ERR_NEEDMOREPARAMS(self.command, actor)
        if actor.is_server():
            self.server = self.actor.get_server()
            return self.from_server(*message.parameters)
        if self.actor.is_user():
            self.user = self.actor.get_user()
            registered = self.user.registered.both
            if not (self.user_registration_command or registered):
                return ERR_NOTREGISTERED(self.actor)
            message.prefix = str(self.user)
            return self.from_user(*message.parameters)
        raise Exception("Don't know what to do :(")

    def _handle_registration(self, actor, message):
        if self.user_registration_command:
            if self.server_registration_command:
                return self.common()
            return self.from_user(*message.parameters)
        if self.server_registration_command:
            return self.from_server(*message.parameters)
        return ERR_NOTREGISTERED(actor)
