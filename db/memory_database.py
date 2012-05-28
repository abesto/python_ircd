from models import User, Channel


class MemoryDatabase(object):
    def __init__(self):
        self.users = {}
        self.channels = {}

    # User management
    def connected(self, nickname, socket):
        return User(nickname, socket)

    def registered(self, user):
        self.users[user.nickname] = user

    def rename(self, old, new):
        self.users[new] = users[old]
        del self.users[old]
        self.users[new].nickname = new

    def disconnected(self, nickname):
        del self.users[nickname]

    def user_exists(self, nickname):
        return nickname in self.users

    def channel_exists(self, channel):
        return channel in self.channels

    def get_user(self, nickname):
        return self.users[nickname]

    def get_channel(self, name):
        if name not in self.channels:
            self.channels[name] = Channel(name)
        return self.channels[name]

    def all_servers(self):
        return []
