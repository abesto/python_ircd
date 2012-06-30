import unittest
from mock import *

from commands.nick import NickCommand
from numeric_responses import *

class TestNickCommand(unittest.TestCase):
    def setUp(self):
        self.db = Mock()

        self.users = [MagicMock(), MagicMock()]
        self.users[0].__str__.return_value = self.users[0].nickname = 'nick0'
        self.users[1].__str__.return_value = self.users[1].nickname = 'nick1'

        self.channel = MagicMock()
        self.channel.__str__.return_value = 'testchannel'

        self.nick = NickCommand()
        self.nick.socket = Mock()
