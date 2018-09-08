import os
from six.moves.configparser import SafeConfigParser
from datetime import datetime
from pydispatch import dispatcher
import logging.config


class SignalingSafeConfigParser(SafeConfigParser):
    def set(self, section, option, value=None):
        SafeConfigParser.set(self, section, option, value)
        dispatcher.send("%s.%s" % (section, option), "config")


config_path = os.path.dirname(__file__)
config = SignalingSafeConfigParser(
    {"created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
)
config.read(os.path.join(config_path, "server.ini"))


def set_decorator(f):
    return f


__all__ = ["config"]

logging.config.fileConfig(os.path.join(config_path, config.get("server", "log_config")))
