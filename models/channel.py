import abnf
from models import Error
from models.base import BaseModel

class ChannelMode(object):
    def __init__(self):
        self.distributed = True
        self.invite_only = False


class Channel(BaseModel):
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

    def get_key(self):
        return str(self)

    def join(self, user):
        self.users.append(user)

    def part(self, user):
        self.users.remove(user)
