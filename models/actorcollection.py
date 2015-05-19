from models.actor import Actor
from models.server import Server
from models.user import User
import models


class Error(models.Error):
    pass


class ActorCollection(object):
    def __init__(self, children):
        self.children = set()
        for child in children:
            if isinstance(child, Actor):
                self.children.add(child)
            elif isinstance(child, User):
                self.children.add(Actor.by_user(child))
            elif isinstance(child, Server):
                self.children.add(Actor.by_server(child))
            elif isinstance(child, ActorCollection):
                self.children += child.children
            else:
                raise Error('Don\'t know what to do with %s' + child.__class__)
        self.children = frozenset(self.children)

    def write(self, message):
        for child in self.children:
            child.write(message)

    def flush(self):
        for child in self.children:
            child.flush()

    def disconnect(self):
        for child in self.children:
            child.disconnect()

    def read(self):
        raise NotImplementedError

    def __str__(self):
        return 'ActorCollection(' +\
               ', '.join([str(child) for child in self.children]) +\
               ')'

    def __repr__(self):
        return 'ActorCollection(' +\
               ', '.join([repr(child) for child in self.children]) +\
               ')'

    def __eq__(self, other):
        return other is ActorCollection and all(
            [actor in other for actor in self.children]
        )

    def __contains__(self, item):
        return item in self.children

    def __iter__(self):
        return iter(self.children)

    def __hash__(self):
        return hash(self.children)
