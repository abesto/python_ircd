import unittest
import mock

from commands.ping import PingCommand

class TestPingCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ping = PingCommand(mock.Mock())
        cls.ping.socket = mock.Mock()

    def test_no_args(self):
        resp = self.ping.from_client()
        self.assertEqual('PONG', resp.command)
        self.assertEqual([], resp.parameters)

    def test_args(self):
        resp = self.ping.from_client('foo')
        self.assertEqual('PONG', resp.command)
        self.assertEqual(['foo'], resp.parameters)
        resp = self.ping.from_client('foo', 'bar')
        self.assertEqual('PONG', resp.command)
        self.assertEqual(['foo', 'bar'], resp.parameters)

