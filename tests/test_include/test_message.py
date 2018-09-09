from unittest import TestCase

from include.message import Message


class TestMessage(TestCase):
    def test_from_string(self):
        msg = Message.from_string(None, "NICK foobar\r\n")
        self.assertEqual(msg.prefix, "")
        self.assertEqual(msg.command, "NICK")
        self.assertEqual(msg.parameters, ["foobar"])
