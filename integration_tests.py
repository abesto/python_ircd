"""
Test-drive a running python-ircd instance via socket communication
with multiple clients.
"""
import errno

import asyncio
import socket
import asynctest
from typing import Optional, List

from application import create_server
from models.database import DEFAULT_DATABASE as db
from config import config


class Client:
    """Socket-based test IRC client"""

    test_case: asynctest.TestCase
    responses: List[List[str]] = []
    timeout = 0.2
    timeout_step = 0.001

    def __init__(self, name: str, test_case: asynctest.TestCase, port: int) -> None:
        self.name = name
        self.test_case = test_case
        self.socket = socket.socket()
        self.socket.connect((config.get("server", "listen_host"), port))
        self.socket.setblocking(False)
        self.socket_file = self.socket.makefile("rw", encoding="UTF-8", newline="\r\n")

    def write(self, msg: str):
        """Send a message to the server"""
        self.responses.append([])
        self.socket_file.write(msg + "\r\n")
        self.socket_file.flush()

    async def expect(self, line: str):
        """Read from the server, and assert that a given message is received (with timeout)"""
        got = None
        timeout = self.timeout
        while got != line and timeout > 0:
            try:
                got = self.socket_file.readline().strip()
                if got != "":
                    self.responses[-1].append(got)
                else:
                    await asyncio.sleep(self.timeout_step)
                    timeout -= self.timeout_step
            except socket.error as exc:
                if exc.errno != errno.EAGAIN:
                    raise
                await asyncio.sleep(self.timeout_step)
                timeout -= self.timeout_step
        self.test_case.assertEqual(got, line)

    def close(self):
        self.socket.close()

    def __str__(self):
        return self.name


class ServerClientTests(asynctest.TestCase):
    """
    Test-drive a running python-ircd instance via socket communication
    with multiple clients.
    """

    async def setUp(self):
        config.set("server", "listen_host", "127.0.0.1")
        config.set("server", "listen_port", "0")
        self.server = await create_server(self.loop)
        self.port = self.server.sockets[0].getsockname()[1]
        self.client_al = Client("al", self, self.port)
        self.client_bob = Client("bob", self, self.port)
        self.client_clair = Client("clair", self, self.port)

    async def tearDown(self):
        self.client_al.close()
        self.client_bob.close()
        self.client_clair.close()
        self.server.close()
        await self.server.wait_closed()
        db.flush()

    async def test_login_nick_first(self, inclient: Optional[Client] = None):
        """Register to the server, sending NICK first then USER"""
        client = inclient or self.client_al
        client.write("NICK %s" % client.name)
        client.write(
            "USER %s %s %s %s"
            % (client.name, client.name, socket.getfqdn(), client.name)
        )
        await client.expect(":localhost 376 %s :End of MOTD command" % client.name)

    async def test_login_user_first(self, inclient: Optional[Client] = None):
        """Register to the server, sending USER first then NICK"""
        client = inclient or self.client_bob
        client.write(
            "USER %s %s %s %s"
            % (client.name, client.name, socket.getfqdn(), client.name)
        )
        client.write("NICK %s" % client.name)
        await client.expect(":localhost 376 %s :End of MOTD command" % client.name)

    async def test_join(self, c=None, channel=None, users=None):
        if c is None:
            c = self.client_al
        if channel is None:
            channel = "#test-chan"
        if users is None:
            users = []
        users.append(c)
        expected_username_list = " ".join([c.name for c in users])
        if len(users) > 1:
            expected_username_list = ":" + expected_username_list
        await self.test_login_nick_first(c)
        c.write("JOIN %s" % channel)
        await c.expect(
            ":localhost 353 %s = %s %s" % (c.name, channel, expected_username_list)
        )
        await c.expect(":localhost 366 %s :End of NAMES list" % c.name)

    async def test_user_list_after_join(self):
        await self.test_join(self.client_al)
        await self.test_join(self.client_bob, users=[self.client_al])

    async def test_message_to_channel(
        self, c=None, rc=None, channel=None, msg="test message"
    ):
        if c is None:
            c = self.client_al
        if channel is None:
            channel = "#test-chan"
        if rc is None:
            if c is self.client_al:
                rc = self.client_bob
            else:
                rc = self.client_al
        await self.test_user_list_after_join()
        c.write("PRIVMSG %s :%s" % (channel, msg))
        await rc.expect(
            ":{c}!{c}@localhost. PRIVMSG {channel} :{msg}".format(
                c=c, channel=channel, msg=msg
            )
        )

    async def test_login_quit_login(self):
        """QUITting releases the nick"""
        await self.test_login_nick_first(self.client_al)
        self.client_al.write("QUIT leaving")
        await self.client_al.expect(":localhost ERROR")
        self.client_al.close()
        self.client_al = Client(self.client_al.name, self, self.port)
        await self.test_login_nick_first(self.client_al)

    async def test_direct_message(self):
        await self.test_login_nick_first(self.client_al)
        await self.test_login_nick_first(self.client_bob)
        msg = "test direct message"
        self.client_al.write("PRIVMSG %s :%s" % (self.client_bob.name, msg))
        await self.client_bob.expect(
            ":{c}!{c}@localhost. PRIVMSG {rc} :{msg}".format(
                c=self.client_al, rc=self.client_bob, msg=msg
            )
        )

    async def test_nick_change(self):
        await self.test_login_nick_first(self.client_al)
        self.client_al.write("NICK foo")
        await self.client_al.expect(
            ":{c}!{c}@localhost. NICK foo".format(c=self.client_al)
        )

    async def test_nick_change_taken(self):
        await self.test_login_nick_first(self.client_al)
        await self.test_login_nick_first(self.client_bob)
        self.client_al.write("NICK %s" % self.client_bob.name)
        await self.client_al.expect(
            ":localhost 433 %s %s :Nickname is already in use"
            % (self.client_al.name, self.client_bob.name)
        )

    async def test_topic(self):
        channel = "#test-channe"
        topic = ":This is the old shit"
        await self.test_join(self.client_al, channel)
        await self.test_join(self.client_bob, channel, [self.client_al])
        self.client_al.write("TOPIC %s %s" % (channel, topic))
        await self.client_bob.expect(
            ":{c}!{c}@localhost. TOPIC {ch} {topic}".format(
                c=self.client_al, ch=channel, topic=topic
            )
        )
        await self.test_join(
            self.client_clair, channel, [self.client_al, self.client_bob]
        )
        await self.client_clair.expect(
            ":localhost 332 {c} {ch} {topic}".format(
                c=self.client_clair, ch=channel, topic=topic
            )
        )

    async def test_clear_topic(self):
        channel = "#test-channel"
        await self.test_join(self.client_al, channel)
        self.client_al.write("TOPIC %s %s" % (channel, ":old topic"))
        self.client_al.write("TOPIC %s :" % channel)
        self.client_al.write("TOPIC %s" % channel)
        await self.client_al.expect(
            ":localhost 331 {c} {ch} :No topic is set".format(
                c=self.client_al.name, ch=channel
            )
        )

    async def test_change_topic_no_such_channel(self):
        await self.test_login_nick_first(self.client_clair)
        self.client_clair.write("TOPIC #foo baz")
        await self.client_clair.expect(
            ":localhost 401 {c} #foo :No such channel".format(c=self.client_clair.name)
        )
