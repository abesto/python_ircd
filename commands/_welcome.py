"""
`welcome`: a helper function used by several commands to send the MOTD
"""
from typing import List

from config import config
from include.message import Message
from include.numeric_replies import (
    RPL_WELCOME,
    RPL_YOURHOST,
    RPL_CREATED,
    RPL_MOTDSTART,
    RPL_MOTD,
    RPL_ENDOFMOTD,
)
from models import Actor


def welcome(actor: Actor) -> List[Message]:
    """Generates a list of `Message` objects representing the MOTD"""
    ret = [
        RPL_WELCOME(actor),
        RPL_YOURHOST(actor),
        RPL_CREATED(actor),
        RPL_MOTDSTART(actor),
    ]
    try:
        with open(config.get("server", "motd_file"), "r") as motd_file:
            ret += [RPL_MOTD(actor, line.strip()) for line in motd_file]
    except IOError:
        pass
    ret.append(RPL_ENDOFMOTD(actor))
    return ret
