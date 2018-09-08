"""
`main`: Main entrypoint of python-ircd. Runs the server.
"""

import logging
import asyncio
from asyncio import StreamReader, StreamWriter

from config import config
from include.connection import Connection
from include.dispatcher import Dispatcher
from include.message import Message, Error as MessageError
from include.router import Router, Error as RouterError
from models import Actor

LOG = logging.getLogger()
DISPATCHER = Dispatcher()
ROUTER = Router()


async def handle(reader: StreamReader, writer: StreamWriter):
    """
    Handle a single connection from a user or another server
    """
    connection = Connection(reader, writer)
    while not Actor.by_connection(connection).disconnected:
        line = await connection.readline()
        if line == "":
            Actor.by_connection(connection).disconnect()
            continue
        try:
            msg = Message.from_string(line)
            LOG.debug("<= %s %s", repr(msg.target), repr(msg))
            resp = DISPATCHER.dispatch(connection, msg)
        except Exception as exc:
            LOG.exception(exc)
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
                    Message(actor, "NOTICE", str(exc)),
                    Message(actor, "NOTICE", "---"),
                    Message(actor, "NOTICE", "Closing connection."),
                ]
                quit_resp = DISPATCHER.dispatch(
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
            await ROUTER.send(resp)
        except RouterError as exc:
            LOG.exception(exc)
            Actor.by_connection(connection).disconnect()


def main():
    """Run the server."""
    host = config.get("server", "listen_host")
    port = config.getint("server", "listen_port")
    LOG.info("Starting server, listening on %s:%s", host, port)

    loop = asyncio.get_event_loop()
    coroutine = asyncio.start_server(handle, host, port, loop=loop)
    loop.run_until_complete(coroutine)
    loop.run_forever()
    coroutine.close()

    LOG.info("Server stopped")


if __name__ == "__main__":
    main()
