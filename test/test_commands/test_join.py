import unittest
from mock import *

from message import Message as M
from numeric_responses import *
from commands.join import JoinCommand


class TestJoinCommand(unittest.TestCase):
    def setUp(self):
        self.channel_patcher = patch('commands.join.Channel')
        self.actorcollection_patcher = patch('commands.join.ActorCollection')
        self.mock_channel = self.channel_patcher.start()
        self.mock_actorcollection = self.actorcollection_patcher.start()

        self.users = [MagicMock(), MagicMock()]
        self.users[0].__str__.return_value = self.users[0].nickname = 'nick0'
        self.users[1].__str__.return_value = self.users[1].nickname = 'nick1'

        self.channel = MagicMock()
        self.channel.__str__.return_value = 'testchannel'

        self.join = JoinCommand()
        self.join.actor = Mock()

    def tearDown(self):
        self.channel_patcher.stop()
        self.actorcollection_patcher.stop()

    def test_normal(self):
        "user1 joining #channel where user0 is already a member, topic is set"
        self.channel.users = self.users
        self.channel.topic = 'channel topic'
        self.join.user = self.users[1]
        self.mock_channel.get.return_value = self.channel

        self.assertListEqual(
            [
                M(self.mock_actorcollection(self.users), 'JOIN', str(self.channel), prefix=self.users[1]),
                RPL_NAMEREPLY(self.join.actor, self.channel),
                RPL_ENDOFNAMES(self.join.actor),
                RPL_TOPIC(self.join.actor, self.channel)
            ],
            self.join.from_user('#channel')
        )


    def test_notopic(self):
        "user1 joining #channel where user0 is already a member, topic isnt set"
        self.channel.users = self.users
        self.channel.topic = None
        self.join.user = self.users[1]
        self.mock_channel.get.return_value = self.channel

        self.assertListEqual(
            [
                M(self.mock_actorcollection(self.users), 'JOIN', str(self.channel), prefix=self.users[1]),
                RPL_NAMEREPLY(self.join.actor, self.channel),
                RPL_ENDOFNAMES(self.join.actor),
            ],
             self.join.from_user('#channel')
        )

        self.channel.join.assert_called_once_with(self.join.user)

    def test_no_such_channel(self):
        models_patcher = patch('commands.join.models')
        models = models_patcher.start()
        class Error(Exception):
            pass
        models.Error  = Error
        self.join.user = self.users[1]
        self.mock_channel.exists.return_value = False
        self.mock_channel.side_effect = Error
        self.assertListEqual(
            [ERR_NOSUCHCHANNEL('#channel', self.join.actor)],
            self.join.from_user('#channel')
        )
        models_patcher.stop()
