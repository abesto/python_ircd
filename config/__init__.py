"""
Access to server configuration. Loads `server.ini` at startup, intializes
logging based on the log file it points to, and sends events via
`pydispatch` when config options are changed by code at runtime.

Does not currently pick up changes from the file-system.
"""

import logging.config
import os
from datetime import datetime
from six.moves.configparser import SafeConfigParser

# pylint: disable=import-error
from pydispatch import dispatcher

__all__ = ["config"]


# pylint: disable=too-many-ancestors
class SignalingSafeConfigParser(SafeConfigParser):
    """
    Extends SafeConfigParser to trigger events via PyDispatcher
    when values change
    """

    def set(self, section, option, value=None):
        SafeConfigParser.set(self, section, option, value)
        dispatcher.send("%s.%s" % (section, option), "config")


CONFIG_PATH = os.path.dirname(__file__)
# pylint: disable=invalid-name
config = SignalingSafeConfigParser(
    {"created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
)
config.read(os.path.join(CONFIG_PATH, "server.ini"))
logging.config.fileConfig(os.path.join(CONFIG_PATH, config.get("server", "log_config")))
