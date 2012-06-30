import unittest
from mock import *

from commands.nick import NickCommand
from commands._welcome import welcome
from numeric_responses import *

class TestNickCommand(unittest.TestCase):
    def setUp(self):
        self.user_patcher = patch('commands.nick.User')
        self.actorcollection_patcher = patch('commands.nick.ActorCollection')
        self.mock_user = self.user_patcher.start()
        self.mock_actorcollection = self.actorcollection_patcher.start()

        self.users = [MagicMock(), MagicMock()]
        self.users[0].__str__.return_value = self.users[0].nickname = 'nick0'
        self.users[1].__str__.return_value = self.users[1].nickname = 'nick1'

        self.channel = MagicMock()
        self.channel.__str__.return_value = 'testchannel'

        self.cmd = NickCommand()
        self.cmd.actor = Mock()

    def tearDown(self):
        self.user_patcher.stop()
        self.actorcollection_patcher.stop()

    def test_no_nick(self):
        self.assertEqual(
            self.cmd.from_user(),
            ERR_NONICKNAMEGIVEN(self.cmd.actor)
        )

    def test_invalid_nick(self):
        self.assertEqual(
            ERR_ERRONEUSNICKNAME('verylongnickname', self.cmd.actor),
            self.cmd.from_user('verylongnickname')
        )
        self.assertEqual(
            ERR_ERRONEUSNICKNAME(u'have_some\1special\300characters!', self.cmd.actor),
            self.cmd.from_user(u'have some\1special\300characters!')
        )

    def test_collision(self):
        self.cmd.actor.user = self.cmd.user = self.users[0]
        self.mock_user.exists.return_value = True
        self.assertEqual(
            ERR_NICKNAMEINUSE('foobar', self.cmd.actor),
            self.cmd.from_user('foobar')
        )
        # User sends NICK with their old nick
        self.cmd.user.registered.both = True
        self.mock_user.get.return_value = self.cmd.user
        self.assertIsNone(self.cmd.from_user(self.cmd.user.nickname))
        self.mock_user.get.assertCalledWith(self.cmd.user.nickname)

    def test_first_command(self):
        "First NICK, USER is not received"
        self.cmd.actor.is_user.return_value = False
        self.mock_user.exists.return_value = False
        user = self.users[0]
        user.registered.nick = False
        user.registered.user = False
        self.mock_user.return_value = user
        self.assertEqual(
            None,
            self.cmd.from_user('nick')
        )
        self.mock_user.assertCalledWidth('nick')
        self.assertTrue(self.cmd.user.registered.nick)

    def test_registration_completed(self):
        "First NICK, USER is received"
        self.cmd.actor.is_user.return_value = True
        self.mock_user.exists.return_value = False
        self.cmd.actor.user = self.cmd.user = user = self.users[0]
        user.registered.nick = False
        user.registered.user = True
        self.assertEqual(
            welcome(self.cmd.actor) + [M(self.cmd.actor, 'NICK', 'nick')],
            self.cmd.from_user('nick')
        )
        self.assertTrue(self.cmd.user.registered.nick)

    def test_second_before_user(self):
        "Non-first NICK, USER is not received"
        self.cmd.actor.is_user.return_value = True
        self.mock_user.exists.return_value = False
        self.cmd.actor.user = self.cmd.user = user = self.users[0]
        user.registered.nick = True
        user.registered.user = False
        self.assertEqual(
            M(self.cmd.actor, 'NICK', 'foobar'),
            self.cmd.from_user('foobar')
        )
        self.assertTrue(self.cmd.user.registered.nick)

    def test_rename(self):
        "Non-first NICK, USER is received"
        server_patcher = patch('commands.nick.Server')
        mock_server = server_patcher.start()
        mock_server.all.return_value = [Mock]

        self.cmd.actor.is_user.return_value = True
        self.mock_user.exists.return_value = False
        self.cmd.actor.user = self.cmd.user = user = self.users[0]
        user.registered.nick = True
        user.registered.user = True
        self.assertEqual(
            M(self.mock_actorcollection([self.cmd.actor] + mock_server.all()), str(user), 'NICK', 'foobar'),
            self.cmd.from_user('foobar')
        )
        server_patcher.stop()
        self.assertTrue(self.cmd.user.registered.nick)

