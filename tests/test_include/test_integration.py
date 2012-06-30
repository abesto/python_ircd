import unittest
from mock import Mock

from include.router import Router
from include.message import Message
from models import Actor, ActorCollection

class ActorDisconnectOnWrite(Actor):
    def write(self, message):
        self.disconnect()

class IntegrationTest(unittest.TestCase):
    def test_actorcollection_disconnect(self):
        shutdown_signal = Mock()
        router = Router(shutdown_signal)

        a0 = ActorDisconnectOnWrite(Mock())
        router.send(Message(a0, 'FOO'))
        a0.socket.shutdown.assert_called_with(shutdown_signal)
        a0.socket.close.assert_called_once()

        col = ActorCollection([
            ActorDisconnectOnWrite(Mock()),
            ActorDisconnectOnWrite(Mock())
        ])

        router.send(Message(col, 'FOO'))
        for actor in col:
            actor.socket.shutdown.assert_called_with(shutdown_signal)
            actor.socket.close.assert_called_once()
