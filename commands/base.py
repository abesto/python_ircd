import models
from numeric_responses import *


class Command(object):
    required_parameter_count = None
    command = None
    must_be_registered = True

    def __init__(self):
        self.message = None
        self.actor = None
        self.user = None
        self.server = None

    def from_server(self, *args):
        raise NotImplementedError

    def from_user(self, *args):
        raise NotImplementedError

    def common(self, *args):
        raise NotImplementedError

    def handle(self, actor, message):
        if self.required_parameter_count is None:
            raise NotImplementedError(
                'required_parameter_count must be set on Handler subclass')
        if self.command is None:
            raise NotImplementedError(
                'command must be set on Handler subclass')
        if self.command != message.command:
            raise "Wrong handler for " + repr(message)
        if actor.is_user() and \
           self.must_be_registered and \
           not actor.get_user().registered.both:
            return ERR_NOTREGISTERED(actor)
        if len(message.parameters) < self.required_parameter_count:
            return ERR_NEEDMOREPARAMS(self.command, actor)

        self.actor = actor
        self.message = message

        if message.command == 'PASS':
            self.common()
        elif actor.is_server() or (not actor.is_user() and message.command == 'SERVICE'):
            self.server = self.actor.get_server()
            return self.from_server(*message.parameters)
        elif self.actor.is_user() or (not actor.is_server() and message.command in ['NICK', 'USER']):
            try:
                self.user = self.actor.get_user()
            except models.Error:
                self.user = None
            message.prefix = str(self.user)
            return self.from_user(*message.parameters)
        else:
            raise Exception('Don\'t know what to do :(')
