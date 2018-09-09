"""
`main`: Main entrypoint of python_ircd. Runs the server.
"""

import logging
import asyncio
from asyncio import StreamReader, StreamWriter

from config import config
from include.connection import Connection, SelfConnection
from include.dispatcher import Dispatcher
from include.message import Message
from include.router import Router, Error as RouterError
from models import db, Actor, Server

LOG = logging.getLogger()
DISPATCHER = Dispatcher()
ROUTER = Router()


async def handle(reader: StreamReader, writer: StreamWriter):
    """
    Handle a single connection from a user or another server
    """
    connection = Connection(reader, writer)
    actor = db.get_or_create(Actor, connection)
    while not connection.disconnected:
        line = await connection.readline()
        if line == "":
            connection.disconnect()
            continue
        # pylint: disable=broad-except
        try:
            msg = Message.from_string(actor, line)
            LOG.debug("<= %s %s", repr(msg.target), repr(msg))
            resp = DISPATCHER.dispatch(connection, msg)
        except Exception as exc:
            LOG.exception(exc)
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
                    Message(actor, "NOTICE", "https://github.com/abesto/python_ircd"),
                    Message(actor, "NOTICE", "---"),
                    Message(actor, "NOTICE", "The message sent by your client was:"),
                    Message(actor, "NOTICE", line.strip("\n")),
                    Message(actor, "NOTICE", "The error was:"),
                    Message(actor, "NOTICE", str(exc)),
                    Message(actor, "NOTICE", "---"),
                    Message(actor, "NOTICE", "Closing connection."),
                ]
                quit_resp = DISPATCHER.dispatch(
                    connection, Message(actor, "QUIT", "Protocol error")
                )
                resp += quit_resp
            else:
                resp = [Message(actor, "ERROR")]
            connection.disconnect()
        # pylint: enable=broad-except

        try:
            await ROUTER.send(resp)
        except RouterError as exc:
            LOG.exception(exc)
            connection.disconnect()


def create_server(loop):
    """Create asyncio coroutine to run the server"""
    host = config.get("server", "listen_host")
    port = config.getint("server", "listen_port")
    LOG.info("Starting server, listening on %s:%s", host, port)
    return asyncio.start_server(handle, host, port, loop=loop)


async def main():
    """Run the server"""
    loop = asyncio.get_event_loop()
    coroutine = await create_server(loop)
    await coroutine.serve_forever()
    loop.run_until_complete(coroutine)
    coroutine.close()

    LOG.info("Server stopped")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
