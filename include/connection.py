"""
Represents an `asyncio` TCP connection, exposing a thin API used across python-ircd
"""
from typing import Any, Tuple
from asyncio import StreamReader, StreamWriter

# pylint: disable=import-error
from pydispatch import dispatcher

# pylint: enable=import-error

from config import config


class Connection:
    """
    Represents an `asyncio` TCP connection, exposing a thin API used across python-ircd.
    Note that there's nothing TCP-specific in the implementation, so in theory the same
    class could be used for other transports as well.
    """

    _writer: StreamWriter
    _reader: StreamReader
    _encoding: str

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.disconnected = False
        self.connection_dropped = False
        self._reader = reader
        self._writer = writer
        self._encoding = "UTF-8"
        self._set_encoding()
        dispatcher.connect(self._set_encoding, "server.encoding", "config")

    def _set_encoding(self):
        self._encoding = config.get("server", "encoding")

    def close(self):
        """Close the connection"""
        return self._writer.close()

    def write(self, data: Any):
        """Serialize any object using `str()`, and write it to the connection"""
        self._writer.write(str(data).encode(self._encoding))

    async def readline(self):
        """Read a full line from the connection"""
        line_bytes = await self._reader.readline()
        return line_bytes.decode(self._encoding)

    def drain(self):
        """Flush the output buffer of the connection"""
        return self._writer.drain()

    def get_peername(self) -> Tuple:
        """Get the “peername” (usually the IP address + port) of the remote end of the connection"""
        return self._writer.transport.get_extra_info("peername")

    def disconnect(self):
        """
        Mark this connection as disconnected.
        Does not actually touch the connection, this is only bookkeeping.
        """
        self.disconnected = True


class SelfConnection(Connection):
    """Dummy `Connection` representing the running server itself"""

    def __init__(self):
        pass

    def close(self):
        raise Exception("SelfConnection.close makes no sense")

    def write(self, data: Any):
        raise Exception("SelfConnection.write makes no sense")

    async def readline(self):
        raise Exception("SelfConnection.readline makes no sense")

    async def drain(self):
        raise Exception("SelfConnection.drain makes no sense")

    def get_peername(self) -> Tuple:
        raise Exception("SelfConnection.get_peername makes no sense")

    def disconnect(self):
        raise Exception("SelfConnection.disonnect makes no sense")
