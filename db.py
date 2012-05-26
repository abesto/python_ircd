import message
import abnf


class Error(Exception): pass


users = {}
channels = {}


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


class Server(object):
    pass


class ChannelMode(object):
    def __init__(self):
        self.distributed = True
        self.invite_only = False

class Channel(object):
    def __init__(self, name):
        raw = abnf.parse(name, abnf.channel)
        if not raw:
            raise Error('Erroneous channel name')
        self.mode = ChannelMode
        self.prefix = raw[0]
        self.id = raw[1] if self.prefix == '!' else None
        self.name = raw[2] if self.prefix == '!' else raw[1]

        self.users = []
        self.topic = None

    def __str__(self):
        return self.prefix + self.name

    def join(self, user):
        self.users.append(user)
    def part(self, user):
        self.users.remove(user)


# User management
def connected(nickname, socket):
    return User(nickname, socket)
def registered(user):
    users[user.nickname] = user
def rename(old, new):
    users[new] = users[old]
    del users[old]
    users[new].nickname = new
def disconnected(nickname):
    del users[nickname]

def user_exists(nickname): return users.has_key(nickname)
def channel_exists(channel): return channels.has_key(channel)

def get_user(nickname): return users[nickname]
def get_channel(name):
    try:
        return channels[name]
    except KeyError:
        channels[name] = Channel(name)
        return channels[name]
def all_servers(): return []
