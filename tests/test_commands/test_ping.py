import unittest

from commands.ping import PingCommand


class TestPingCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ping = PingCommand()

    def test_no_args(self):
        resp = self.ping.from_user()
        self.assertEqual("PONG", resp.command)
        self.assertEqual([], resp.parameters)

    def test_args(self):
        resp = self.ping.from_user("foo")
        self.assertEqual("PONG", resp.command)
        self.assertEqual(["foo"], resp.parameters)
        resp = self.ping.from_user("foo", "bar")
        self.assertEqual("PONG", resp.command)
        self.assertEqual(["foo", "bar"], resp.parameters)
