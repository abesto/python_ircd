from models.base import BaseModel


class User(BaseModel):
    def __init__(self, nickname):
        self.nickname = nickname
        self.channels = []

        self.hostname = None
        self.username = None
        self.realname = None

        self.registered = RegistrationStatus()

        self.mode = UserMode()
        self.away = False

    def get_key(self):
        return self.nickname

    def rename(self, to):
        self.set_key(to)

    def join(self, channel):
        if channel not in self.channels:
            self.channels.append(channel)
            channel.join(self)

    def part(self, channel):
        if channel in self.channels:
            self.channels.remove(channel)
            channel.part(self)

    def delete(self):
        for channel in self.channels:
            self.part(channel)

    def _set_key(self, new_key):
        self.nickname = new_key

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

