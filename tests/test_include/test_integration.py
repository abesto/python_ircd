import asynctest
from mock import Mock

from include.message import Message
from include.router import Router
from models import Actor, ActorCollection


class ActorDisconnectOnWrite(Actor):
    def write(self, message):
        self.disconnect()


class IntegrationTest(asynctest.TestCase):
    async def test_actorcollection_disconnect(self):
        router = Router()

        a0 = ActorDisconnectOnWrite(Mock())
        await router.send(Message(a0, "FOO"))
        a0.connection.close.assert_called_with()

        col = ActorCollection(
            [ActorDisconnectOnWrite(Mock()), ActorDisconnectOnWrite(Mock())]
        )

        await router.send(Message(col, "FOO"))
        for actor in col:
            actor.connection.close.assert_called_with()
