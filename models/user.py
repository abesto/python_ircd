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
        super(User, self).delete()

    def _set_key(self, new_key):
        self.nickname = new_key

    def __str__(self):
        return "%s!%s@%s" % (self.nickname, self.username, self.hostname)

    def __repr__(self):
        return str(self)


class UserMode:
    away = False
    invisible = False
    wallops = False
    restricted = False
    operator = False
    local_operator = False
    notices = False


# pylint: disable=too-few-public-methods
class RegistrationStatus:
    """Represents the registration state of a user"""

    def __init__(self, *, nick: bool = False, user: bool = False) -> None:
        self.nick: bool = nick
        self.user: bool = user

    @property
    def both(self):
        """True iff `self.nick and self.user`"""
        return self.nick and self.user

    def __hash__(self) -> int:
        return int(self.nick) + 2 * int(self.user)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, RegistrationStatus):
            return False
        return self.nick == o.nick and self.user == o.user


# pylint: enable=too-few-public-methods
