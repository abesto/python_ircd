import unittest
import socket
import time
import errno

from config import config


class Client(object):
    test_case = None
    timeout = 0.2
    timeout_step = 0.001

    def __init__(self, name):
        self.name = name
        self.socket = socket.socket()
        self.socket.connect((config.get('server', 'listen_host'), config.getint('server', 'listen_port')))
        self.socket.setblocking(0)
        self.socket_file = self.socket.makefile()
        self.responses = []

    def write(self, msg):
        self.responses.append([])
        print '<- [%s] %s' % (self.name, msg)
        self.socket_file.write(msg + '\r\n')
        self.socket_file.flush()

    def expect(self, line):
        got = None
        timeout = self.timeout
        while got != line and timeout > 0:
            try:
                got = self.socket_file.readline().strip()
                self.responses[-1].append(got)
                print '-> [%s] %s' % (self.name, got)
            except socket.error, e:
                if e.errno != errno.EAGAIN:
                    raise
                time.sleep(self.timeout_step)
                timeout -= self.timeout_step
        self.test_case.assertEqual(got, line)

    def __str__(self):
        return self.name


class ServerClientTests(unittest.TestCase):
    n = 0

    @classmethod
    def setUpClass(cls):
        Client.test_case = None

    @classmethod
    def _increment_n(cls):
        cls.n += 1

    def setUp(self):
        self._increment_n()
        self.c1 = Client('al-%s' % self.n)
        self.c2 = Client('bob-%s' % self.n)
        self.c3 = Client('clair-%s' % self.n)
        Client.test_case = self

    def test_login_nick_first(self, c=None):
        if c is None: c = self.c1
        c.write('NICK %s' % c.name)
        c.write('USER %s %s %s %s' % (c.name, c.name, socket.getfqdn(), c.name))
        c.expect(':localhost 376 %s :End of MOTD command' % c.name)

    def test_login_user_first(self, c=None):
        if c is None: c = self.c2
        c.write('USER %s %s %s %s' % (c.name, c.name, socket.getfqdn(), c.name))
        c.write('NICK %s' % c.name)
        c.expect(':localhost 376 %s :End of MOTD command' % c.name)

    def test_join(self, c=None, channel=None, users=None):
        if c is None: c = self.c1
        if channel is None: channel = '#ch-%s' % self.n
        if users is None: users = []
        users.append(c)
        expected_username_list = ' '.join([c.name for c in users])
        if len(users) > 1:
            expected_username_list = ':' + expected_username_list
        self.test_login_nick_first(c)
        c.write('JOIN %s' % channel)
        c.expect(':localhost 353 %s = %s %s' % (c.name, channel, expected_username_list))
        c.expect(':localhost 366 %s :End of NAMES list' % c.name)

    def test_user_list_after_join(self):
        self.test_join(self.c1)
        self.test_join(self.c2, users=[self.c1])

    def test_message_to_channel(self, c=None, rc=None, channel=None, msg='test message'):
        if c is None: c = self.c1
        if channel is None: channel = '#ch-%s' % self.n
        if rc is None:
            if c is self.c1: rc = self.c2
            else: rc = self.c1
        self.test_user_list_after_join()
        c.write('PRIVMSG %s :%s' % (channel, msg))
        rc.expect(':{c}!{c}@localhost. PRIVMSG {channel} :{msg}'.format(
            c=c, channel=channel, msg=msg))

    def test_login_quit_login(self):
        """QUITting releases the nick"""
        self.test_login_nick_first(self.c1)
        self.c1.write('QUIT leaving')
        self.c1.expect(':localhost ERROR')
        self.c1 = Client(self.c1.name)
        self.test_login_nick_first(self.c1)

    def test_direct_message(self):
        self.test_login_nick_first(self.c1)
        self.test_login_nick_first(self.c2)
        msg = 'test direct message'
        self.c1.write('PRIVMSG %s :%s' % (self.c2.name, msg))
        self.c2.expect(':{c}!{c}@localhost. PRIVMSG {rc} :{msg}'.format(
            c=self.c1, rc=self.c2, msg=msg))

    def test_nick_change(self):
        self.test_login_nick_first(self.c1)
        self.c1.write('NICK foo')
        self.c1.expect(':{c}!{c}@localhost. NICK foo'.format(c=self.c1))

    def test_nick_change_taken(self):
        self.test_login_nick_first(self.c1)
        self.test_login_nick_first(self.c2)
        self.c1.write('NICK %s' % self.c2.name)
        self.c1.expect(':localhost 433 %s %s :Nickname is already in use' % (self.c1.name, self.c2.name))

    def test_topic(self):
        channel = '#ch-%s' % self.n
        topic = ':This is the old shit'
        self.test_join(self.c1, channel)
        self.test_join(self.c2, channel, [self.c1])
        self.c1.write('TOPIC %s %s' % (channel, topic))
        self.c2.expect(':{c}!{c}@localhost. TOPIC {ch} {topic}'.format(
            c=self.c1, ch=channel, topic=topic))
        self.test_join(self.c3, channel, [self.c1, self.c2])
        self.c3.expect(':localhost 332 {c} {ch} {topic}'.format(
            c=self.c3, ch=channel, topic=topic))

    def test_clear_topic(self):
        channel = '#ch-%s' % self.n
        self.test_join(self.c1, channel)
        self.c1.write('TOPIC %s %s' % (channel, ':old topic'))
        self.c1.write('TOPIC %s :' % channel)
        self.c1.write('TOPIC %s' % channel)
        self.c1.expect(':localhost 331 {c} {ch} :No topic is set'.format(
            c=self.c1.name, ch=channel))

