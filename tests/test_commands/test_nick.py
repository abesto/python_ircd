import unittest
from mock import *

from commands.nick import NickCommand
from commands._welcome import welcome
from include.numeric_responses import *
from include.message import Message as M
import models


class TestNickCommand(unittest.TestCase):
    def setUp(self):
        self.setup_mocks()
        self.setup_users()
        self.setup_actor()
        self.setup_cmd()
        self.registered(user=False, nick=False)
        self.nickname_available()

    def tearDown(self):
        self.teardown_mocks()

    def test_no_nick(self):
        self.assertEqual(self.cmd.from_user(), ERR_NONICKNAMEGIVEN(self.cmd.actor))

    def test_invalid_nick(self):
        for nick in ["verylongnickname", u"\1special\300"]:
            self.assertEqual(
                ERR_ERRONEUSNICKNAME(nick, self.actor), self.cmd.from_user(nick)
            )

    def test_collision(self):
        "Nickname collision"
        self.nickname_unavailable()
        self.assertEqual(
            ERR_NICKNAMEINUSE(self.users[1].nickname, self.cmd.actor),
            self.cmd.from_user(self.users[1].nickname),
        )

    def test_rename_same(self):
        "NICK to the already set nickname"
        self.registered(user=True, nick=True)
        self.nickname_unavailable()
        self.mock_user.get.return_value = self.user
        self.assertIsNone(self.cmd.from_user(self.user.nickname))
        self.mock_user.get.assert_called_with(self.user.nickname)

    def test_first_nick(self):
        "First NICK, USER is not received"
        self.mock_user.return_value = self.user
        self.assertIsNone(self.cmd.from_user("nick"))
        self.mock_user.assert_called_with("nick")
        self.assertTrue(self.cmd.user.registered.nick)

    def test_second_nick_before_user(self):
        "Non-first NICK, USER is not received"
        self.registered(nick=True)
        self.assertEqual(M(self.actor, "NICK", "foobar"), self.cmd.from_user("foobar"))
        self.assertTrue(self.user.registered.nick)

    def test_registration_completed(self):
        "First NICK, USER is received"
        self.registered(user=True)
        self.assertEqual(
            welcome(self.actor) + [M(self.actor, "NICK", "nick")],
            self.cmd.from_user("nick"),
        )
        self.assertTrue(self.user.registered.nick)

    @patch("commands.nick.Server")
    def test_rename(self, mock_server):
        "User already registered, changes nickname"
        mock_server.all.return_value = [Mock]
        self.registered(user=True, nick=True)

        self.actor.channels = channels = [MagicMock(), MagicMock()]
        for idx, channel in enumerate(channels):
            channel.__str__.return_value = "testchannel" + str(idx)
            channel.users = [Mock(), Mock()]

        self.assertEqual(
            M(
                self.mock_actorcollection(
                    [self.actor]
                    + mock_server.all()
                    + channels[0].users
                    + channels[1].users
                ),
                "NICK",
                "foobar",
                prefix=str(self.user),
            ),
            self.cmd.from_user("foobar"),
        )

    def registered(self, user=None, nick=None):
        if user is not None:
            self.user.registered.user = user
        if nick is not None:
            self.user.registered.nick = nick
        self.actor.is_user.return_value = (
            self.user.registered.user or self.user.registered.nick
        )

    def nickname_unavailable(self):
        self.mock_user.get.return_value = self.users[1]
        self.mock_user.get.side_effect = None
        self.mock_user.exists.return_value = True

    def nickname_available(self):
        self.mock_user.get.side_effect = models.Error()
        self.mock_user.exists.return_value = False

    def setup_mocks(self):
        self.user_patcher = patch("commands.nick.User")
        self.actorcollection_patcher = patch("commands.nick.ActorCollection")
        self.mock_user = self.user_patcher.start()
        self.mock_actorcollection = self.actorcollection_patcher.start()

    def setup_users(self):
        self.users = [MagicMock(), MagicMock()]
        for idx, user in enumerate(self.users):
            user.__str__.return_value = user.nickname = "nick" + str(idx)
        self.user = self.users[0]

    def setup_actor(self):
        self.actor = Mock()
        self.actor.user = self.user

    def setup_cmd(self):
        self.cmd = NickCommand()
        self.cmd.actor = self.actor
        self.cmd.user = self.user

    def teardown_mocks(self):
        self.user_patcher.stop()
        self.actorcollection_patcher.stop()
