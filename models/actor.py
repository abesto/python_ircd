import message
from models import Error
from models.base import BaseModel


class Actor(BaseModel):
    socket_to_actor = {}

    def __init__(self, socket, **kwargs):
        self.password = None
        self.disconnected = False

        self.socket = socket
        self.socket_file = socket.makefile('rw')

        self._server = None
        self._user = None
        if kwargs.has_key('user'):
            self.user = kwargs['user']
        if kwargs.has_key('server'):
            self.server = kwargs['server']

    # Model stuff
    def get_key(self):
        return self.socket

    @staticmethod
    def by_socket(socket):
        try:
            return Actor.get(socket)
        except Error:
            actor = Actor(socket)
            actor.save()
            return actor

    @staticmethod
    def by_user(user):
        return user.actor

    # Union of User and Server
    def is_user(self):
        return self._user is not None

    def is_server(self):
        return self._server is not None

    def get_user(self):
        if not self.is_user():
            raise Error('not a user')
        return self._user

    def get_server(self):
        if not self.is_server():
            raise Error('not a server')
        return self._server

    def __setattr__(self, key, value):
        if key == 'server':
            if self.is_user():
                raise Error('only one of user and server may be passed to Actor')
            if value.actor:
                raise Error('server already has an actor set')
            self._server = value
            self._server.actor = self
        elif key == 'user':
            if self.is_server():
                raise Error('only one of user and server may be passed to Actor')
            if hasattr(value, 'actor'):
                raise Error('user already has an actor set')
            self._user = value
            self._user.actor = self
        else:
            super(BaseModel, self).__setattr__(key, value)

    def __str__(self):
        if self.is_user():
            return 'Actor(' + str(self.get_user()) + ')'
        elif self.is_server():
            return 'Actor(' + str(self.get_server()) + ')'
        else:
            return 'Unknown Actor'

    def __repr__(self):
        return str(self)

    # Implement socket-like interface
    def write(self, message):
        if self.is_user() and message.add_nick:
            message.parameters.insert(0, self.get_user().nickname)
        self.socket_file.write(message)
        if self.is_user() and message.add_nick:
            message.parameters = message.parameters[1:]

    def flush(self):
        self.socket_file.flush()

    def read(self):
        msg = message.from_string(self.socket_file.readline())
        msg.sender = self
        return msg

    def disconnect(self):
        self.disconnected = True

    def __iter__(self):
        return iter([self])

