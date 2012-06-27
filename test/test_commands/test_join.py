import unittest
from mock import *

from message import Message as M
from models import Error as ModelError
from numeric_responses import *
from commands.join import JoinCommand


class TestJoinCommand(unittest.TestCase):
    def setUp(self):
        self.db = Mock()

        self.users = [MagicMock(), MagicMock()]
        self.users[0].__str__.return_value = self.users[0].nickname = 'nick0'
        self.users[1].__str__.return_value = self.users[1].nickname = 'nick1'

        self.channel = MagicMock()
        self.channel.__str__.return_value = 'testchannel'

        self.join = JoinCommand(self.db)
        self.join.socket = Mock()

    def test_normal(self):
        "user1 joining #channel where user0 is already a member, topic is set"
        self.channel.users = self.users
        self.channel.topic = 'channel topic'
        self.join.user = self.users[1]
        self.db.get_channel.return_value = self.channel

        self.assertListEqual(
            [
                M(self.users, 'JOIN', str(self.channel), prefix=self.users[1]),
                RPL_NAMEREPLY(self.join.user, self.channel),
                RPL_ENDOFNAMES(self.join.user),
                RPL_TOPIC(self.join.user, self.channel)
            ],
            self.join.from_client('#channel')
        )

        self.channel.join.assert_called_once_with(self.join.user)

    def test_notopic(self):
        "user1 joining #channel where user0 is already a member, topic isnt set"
        self.channel.users = self.users
        self.channel.topic = None
        self.join.user = self.users[1]
        self.db.get_channel.return_value = self.channel

        self.assertListEqual(
            [
                M(self.users, 'JOIN', str(self.channel), prefix=self.users[1]),
                RPL_NAMEREPLY(self.join.user, self.channel),
                RPL_ENDOFNAMES(self.join.user),
            ],
             self.join.from_client('#channel')
        )

        self.channel.join.assert_called_once_with(self.join.user)

    def test_no_such_channel(self):
        self.join.user = self.users[1]
        self.db.get_channel.side_effect = ModelError()
        self.assertListEqual(
            [ERR_NOSUCHCHANNEL('#channel', self.join.user)],
            self.join.from_client('#channel')
        )
