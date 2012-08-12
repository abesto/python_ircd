from include import abnf

from models import Error
from models.base import BaseModel

class ChannelMode(object):
    def __init__(self):
        self.distributed = True
        self.invite_only = False


class Channel(BaseModel):
    def __init__(self, name):
        if not self.is_valid_name(name):
            raise Error('Erroneous channel name')

        raw = abnf.parse(name, abnf.channel)
        self.mode = ChannelMode
        self.prefix = raw[0]
        self.id = raw[1] if self.prefix == '!' else None
        self.name = raw[2] if self.prefix == '!' else raw[1]

        self.users = []
        self.topic = None

    def __str__(self):
        return self.prefix + self.name

    @staticmethod
    def is_valid_name(name):
        return bool(abnf.parse(name, abnf.channel))

    def get_key(self):
        return str(self)

    def join(self, user):
        if user not in self.users:
            self.users.append(user)
            user.join(self)


    def part(self, user):
        if user in self.users:
            self.users.remove(user)
            user.part(self)
