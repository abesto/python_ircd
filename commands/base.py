from numeric_responses import *


class Command(object):
    required_parameter_count = None
    command = None
    must_be_registered = True

    def __init__(self, db):
        self.socket = None
        self.message = None
        self.user = None
        self.server = None
        self.db = db

    def handle_from_server(self, *args):
        raise NotImplementedError

    def from_client(self, *args):
        raise NotImplementedError

    def handle(self, socket, message):
        if self.required_parameter_count is None:
            raise NotImplementedError(
                'required_parameter_count must be set on Handler subclass')
        if self.command is None:
            raise NotImplementedError(
                'command must be set on Handler subclass')
        if self.command != message.command:
            raise "Wrong handler for " + repr(message)
        if isinstance(socket.client, self.db.User) and \
           self.must_be_registered and \
           not socket.client.registered.both:
            return ERR_NOTREGISTERED(socket.client)
        if len(message.parameters) < self.required_parameter_count:
            return ERR_NEEDMOREPARAMS(self.command, socket.client)

        self.socket = socket
        self.message = message
        if isinstance(socket.client, self.db.Server):
            self.server = socket.client
            return self.handle_from_server(*message.parameters)
        else:
            self.user = socket.client
            message.prefix = str(self.user)
            return self.from_client(*message.parameters)
