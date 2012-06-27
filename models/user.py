import message

class User(object):
    def __init__(self, nickname, socket):
        self.nickname = nickname
        self.channels = []
        self.socket = socket
        self.socket_file = self.socket.makefile('rw')
        self.socket.client = self

        self.hostname = None
        self.username = None
        self.realname = None

        self.registered = RegistrationStatus()

        self.mode = UserMode()
        self.away = False

    def write(self, message):
        self.socket_file.write(message)

    def flush(self):
        self.socket_file.flush()

    def read(self):
        msg = message.from_string(self.socket_file.readline())
        msg.sender = self
        return msg

    def disconnect(self):
        self.socket_file.close()
        self.socket.close()

    def __str__(self):
        return '%s!%s@%s' % (self.nickname, self.username, self.hostname)

    def __repr__(self):
        return str(self)


class UserMode(object):
    away = False
    invisible = False
    wallops = False
    restricted = False
    operator = False
    local_operator = False
    notices = False


class RegistrationStatus(object):
    def __init__(self):
        self.nick = False
        self.user = False

    def __getattr__(self, item):
        if item == 'both':
            return self.nick and self.user
        else:
            raise AttributeError


