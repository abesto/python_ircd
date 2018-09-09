import unittest
from mock import *

from commands.join import JoinCommand
from include.message import Message as M
from include.numeric_replies import *


class TestJoinCommand(unittest.TestCase):
    def setUp(self):
        self.setup_users()
        self.setup_channel()
        self.setup_join_command()
        self.setup_mocks()

    def tearDown(self):
        self.teardown_mocks()

    def test_with_topic(self):
        self.join_success(
            channel_topic="channel topic",
            response_builder=self.joined_with_topic_response,
        )

    def test_without_topic(self):
        self.join_success(
            channel_topic=None, response_builder=self.joined_without_topic_response
        )

    def test_no_such_channel(self):
        self.mock_channel.is_valid_name.return_value = False
        self.assertListEqual(
            self.run_command(), [ERR_NOSUCHCHANNEL(self.channel.name, self.cmd.actor)]
        )

    def join_success(self, channel_topic, response_builder):
        self.channel.topic = channel_topic
        actual_response = self.run_command()
        expected_response = response_builder()
        self.assertListEqual(actual_response, expected_response)
        self.channel.join.assert_called_once_with(self.cmd.user)

    def run_command(self):
        return self.cmd.from_user(self.channel.name)

    def joined_without_topic_response(self):
        return [
            M(
                self.mock_actorcollection(self.users),
                "JOIN",
                str(self.channel),
                prefix=self.joining_user,
            ),
            RPL_NAMEREPLY(self.cmd.actor, self.channel),
            RPL_ENDOFNAMES(self.cmd.actor),
        ]

    def joined_with_topic_response(self):
        return self.joined_without_topic_response() + [
            RPL_TOPIC(self.cmd.actor, self.channel)
        ]

    def setup_users(self):
        self.old_user = self.create_user("old")
        self.joining_user = self.create_user("joining")
        self.users = [self.old_user, self.joining_user]

    def setup_channel(self):
        self.channel = MagicMock()
        self.channel.name = "#channel"
        self.channel.__str__.return_value = self.channel.name
        self.channel.users = self.users

    def setup_join_command(self):
        self.cmd = JoinCommand()
        self.cmd.actor = MagicMock()
        self.cmd.actor.__str__.return_value = "actor"
        self.cmd.user = self.joining_user

    def create_user(self, nick):
        user = MagicMock()
        user.__str__.return_value = user.nickname = nick
        return user

    def setup_mocks(self):
        self.channel_patcher = patch("commands.join.Channel")
        self.actorcollection_patcher = patch("commands.join.ActorCollection")
        self.db_patcher = patch("commands.join.db")
        self.mock_channel = self.channel_patcher.start()
        self.mock_actorcollection = self.actorcollection_patcher.start()
        self.mock_db = self.db_patcher.start()
        self.mock_db.get_or_create.return_value = self.channel

    def teardown_mocks(self):
        self.channel_patcher.stop()
        self.actorcollection_patcher.stop()
        self.db_patcher.stop()
