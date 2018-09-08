# -*- coding: utf-8 -*-

import asyncio
import logging
from asyncio import StreamReader, StreamWriter

log = logging.getLogger()

from config import config

from include.connection import Connection
from include.dispatcher import Dispatcher
from include.message import Message
from include.router import Router

from models import Actor

dispatcher = Dispatcher()
router = Router()


async def handle(reader: StreamReader, writer: StreamWriter):
    connection = Connection(reader, writer)
    while not Actor.by_connection(connection).disconnected:
        line = await connection.readline()
        if line == "":
            Actor.by_connection(connection).disconnect()
            continue
        try:
            msg = Message.from_string(line)
            log.debug("<= %s %s" % (repr(msg.target), repr(msg)))
            resp = dispatcher.dispatch(connection, msg)
        except Exception as e:
            log.exception(e)
            actor = Actor.by_connection(connection)
            if (
                actor.is_user()
                and actor.get_user().registered.nick
                and actor.get_user().registered.user
            ):
                resp = [
                    Message(
                        actor,
                        "NOTICE",
                        "The message your client has just sent could not be parsed or processed.",
                    ),
                    Message(
                        actor,
                        "NOTICE",
                        "If this is a problem with the server, please open an issue at:",
                    ),
                    Message(actor, "NOTICE", "https://github.com/abesto/python-ircd"),
                    Message(actor, "NOTICE", "---"),
                    Message(actor, "NOTICE", "The message sent by your client was:"),
                    Message(actor, "NOTICE", line.strip("\n")),
                    Message(actor, "NOTICE", "The error was:"),
                    Message(actor, "NOTICE", str(e)),
                    Message(actor, "NOTICE", "---"),
                    Message(actor, "NOTICE", "Closing connection."),
                ]
                quit_resp = dispatcher.dispatch(
                    connection, Message(None, "QUIT", "Protocol error")
                )
                if isinstance(quit_resp, list):
                    resp += quit_resp
                else:
                    resp.append(quit_resp)
            else:
                resp = Message(actor, "ERROR")
            Actor.by_connection(connection).disconnect()

        try:
            await router.send(resp)
        except Exception as e:
            log.exception(e)
            Actor.by_connection(connection).disconnect()


host = config.get("server", "listen_host")
port = config.getint("server", "listen_port")
log.info("Starting server, listening on %s:%s" % (host, port))

loop = asyncio.get_event_loop()
coroutine = asyncio.start_server(handle, host, port, loop=loop)
server = loop.run_until_complete(coroutine)
loop.run_forever()

log.info("Server stopped")
