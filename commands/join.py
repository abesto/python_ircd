"""
`JoinCommand`: implements the JOIN IRC command
"""
from collections import defaultdict

from typing import List, Optional, DefaultDict

from commands.base import Command
from include.flatten import flatten
from include.message import Message
from include.numeric_replies import (
    ERR_NOSUCHCHANNEL,
    RPL_NAMEREPLY,
    RPL_ENDOFNAMES,
    RPL_TOPIC,
)
from models import db, ActorCollection, Channel

__all__ = ["JoinCommand"]


class Parameters:
    """
    Encapsulates logic for parsing arguments specific to JOIN

    Parameters: <channel>{,<channel>} [<key>{,<key>}]
    """

    def __init__(self, channels: str, keys_str: str) -> None:
        self.part_all = False
        self.channel_names: List[str] = []
        self.keys: List[str] = []
        self.key_dict: DefaultDict[str, Optional[str]] = defaultdict(lambda: None)

        self.parse_channels(channels)
        self.parse_keys(keys_str)
        self.build_key_dict()

    def parse_channels(self, channels: str):
        """
        Comma-separated list of channel names. The special value `0` means
        the user wants to leave all channels.
        """
        if channels == "0":
            self.part_all = True
        else:
            self.channel_names = channels.split(",")

    def parse_keys(self, keys_str: str):
        """
        The first argument after the channel names is a comma-separated
        list of channel keys (passwords)
        """
        self.keys = keys_str.split(",")

    def build_key_dict(self):
        """
        Populate a dictionary to look up a channel key by channel name
        """
        self.key_dict.update(zip(self.channel_names, self.keys))

    def get_key_for_channel_name(self, name: str) -> Optional[str]:
        """Look up channel key by name"""
        return self.key_dict[name]


class JoinCommand(Command):
    """
    Implements the JOIN IRC command
    https://tools.ietf.org/html/rfc1459#section-4.2.1
    """

    required_parameter_count = 1
    command = "JOIN"

    def __init__(self):
        super().__init__()
        self.parameters: Parameters = None

    # pylint: disable=arguments-differ,keyword-arg-before-vararg
    def from_user(
        self, channel_names_str: str = "", keys_str: str = "", *_
    ) -> List[Message]:
        """
        `JOIN 0` leaves all channels
        `JOIN <channel>{,<channel>} [<key>{,<key>}]` makes the user join all
        the specified channels. Channel key verification is not currently implemented.
        """
        self.parameters = Parameters(channel_names_str, keys_str)
        if self.parameters.part_all:
            return self.part_all_channels()
        return flatten(
            [
                self.join_or_error(channel_name)
                for channel_name in self.parameters.channel_names
            ]
        )

    # pylint: enable=arguments-differ,keyword-arg-before-vararg

    def from_server(self, *args):
        raise Exception("IRC: Server Protocol (RFC2813) is not (yet?) implemented")

    def join_or_error(self, channel_name: str) -> List[Message]:
        """Join a specific channel, or return an error on failure"""
        if Channel.is_valid_name(channel_name):
            return self.join(channel_name)
        return self.no_such_channel_message(channel_name)

    def join(self, channel_name: str) -> List[Message]:
        """Verify channel key and join the channel"""
        channel = db.get_or_create(Channel, channel_name)
        if self.got_valid_key_for(channel):
            channel.join(self.user)
            return self.join_message(channel)
        return self.invalid_key_message(channel)

    # pylint: disable=no-self-use
    def part_all_channels(self) -> List[Message]:
        """Make the user leave all channels"""
        # TODO implement `part_all_channels`
        return []

    # pylint: enable=no-self-use

    # pylint: disable=no-self-use,unused-argument
    def got_valid_key_for(self, channel: Channel) -> bool:
        """Verify that the channel key received for `channel` is correct"""
        # TODO based on self.parameters.get_key_for_channel_name and channel
        return True

    # pylint: enable=no-self-use,unused-argument

    def no_such_channel_message(self, channel_name: str) -> List[Message]:
        """Instantiate `ERR_NOSUCHCHANNEL"""
        return [ERR_NOSUCHCHANNEL(channel_name, self.actor)]

    # pylint: disable=no-self-use,unused-argument
    def invalid_key_message(self, channel: Channel) -> List[Message]:
        """TODO implement invalid_key_message"""
        return []

    # pylint: enable=no-self-use,unused-argument

    def join_message(self, channel: Channel) -> List[Message]:
        """
        Generate `Message`s triggered by a successful JOIN:

         * Tell everyone in the affected channel about the JOIN
         * Tell the user who's joining the full list of users currently on the channel
         * Tell the user who's joining the topic of the channel, if it's set
        """
        ret = [
            Message(
                ActorCollection(channel.users), "JOIN", str(channel), prefix=self.user
            ),
            RPL_NAMEREPLY(self.actor, channel),
            RPL_ENDOFNAMES(self.actor),
        ]
        if channel.topic is not None:
            ret.append(RPL_TOPIC(self.actor, channel))
        return ret
