import unittest
from mock import *

from commands.user import UserCommand
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

        self.cmd = UserCommand()
        self.cmd.actor = MagicMock()

    def tearDown(self):
        self.user_patcher.stop()
        self.actorcollection_patcher.stop()

    def test_first_command(self):
        "NICK is not received"
        self.cmd.actor.is_user.return_value = False
        user = Mock()
        user.registered.nick = False
        user.registered.user = False
        self.mock_user.return_value = user
        self.assertEqual(
            None,
            self.cmd.from_user('username', 'hostname', 'servername', 'realname')
        )
        self.mock_user.assertCalledWidth('nick')
        self.assertTrue(self.cmd.user.registered.user)

    def test_after_nick(self):
        "NICK is received"
        server_patcher = patch('commands.nick.Server')
        mock_server = server_patcher.start()
        mock_server.all.return_value = [Mock]

        self.cmd.actor.is_user.return_value = True
        self.cmd.actor.user = self.cmd.user = user = self.users[0]
        user.registered.nick = True
        user.registered.user = False
        self.assertEqual(
            welcome(self.cmd.actor),
            self.cmd.from_user('username', 'hostname', 'servername', 'realname')
        )
        self.assertTrue(self.cmd.user.registered.user)

    def test_already_registered(self):
        self.cmd.actor.is_user.return_value = True
        self.cmd.actor.user = self.cmd.user = user = self.users[0]
        user.registered.nick = False
        user.registered.user = True
        self.assertEqual(
            ERR_ALREADYREGISTRED(self.cmd.actor),
            self.cmd.from_user('username', 'hostname', 'servername', 'realname')
        )

