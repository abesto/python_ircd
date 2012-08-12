from include.numeric_responses import *
from include.message import Message as M

from models.channel import Channel
from models.actorcollection import ActorCollection

from commands.base import Command


class Parameters:
    def __init__(self, channels, keys):
        self.parse_channels(channels)
        self.parse_keys(keys)
        self.build_key_dict()

    def parse_channels(self, channels):
        self.part_all = (channels == '0')
        self.set_channels(channels)

    def parse_keys(self, keys):
        self.keys = keys.split(',')

    def set_channels(self, channels):
        if self.part_all:
            self.channel_names = []
        else:
            self.channel_names = channels.split(',')

    def build_key_dict(self):
        self.key_dict = dict(zip(
            self.channel_names,
            self.keys + [None] * (len(self.channel_names) - len(self.keys))
        ))

    def get_key_for_channel_name(self, name):
        if name in self.key_dict:
            return self.key_dict[name]
        return None


class PartitionedChannelNames:
    def __init__(self, valid, invalid):
        self.valid = valid
        self.invalid = invalid

    @classmethod
    def from_list(cls, names):
        valid = []
        invalid = []
        for name in names:
            if Channel.is_valid_name(name):
                valid.append(name)
            else:
                invalid.append(name)
        return PartitionedChannelNames(valid, invalid)


class JoinCommand(Command):
    required_parameter_count = 1
    command = 'JOIN'

    def from_user(self, channel_names_str, keys_str='', *_):
        self.parameters = Parameters(channel_names_str, keys_str)
        if self.parameters.part_all:
            return self.part_all_channels()
        return self.join_channels()

    def join_channels(self):
        self.partition_channel_names()
        ret = []
        for channel_name in self.partitioned_channel_names.valid:
            ret += self.join(channel_name)
        for channel_name in self.partitioned_channel_names.invalid:
            ret += self.no_such_channel_message(channel_name)
        return ret

    def join(self, channel_name):
        channel = self.get_channel(channel_name)
        if self.got_valid_key_for(channel):
            channel.join(self.user)
            return self.join_message(channel)
        return self.invalid_key_message(channel)

    def part_all_channels(self):
        # TODO
        pass

    def partition_channel_names(self):
        self.partitioned_channel_names = PartitionedChannelNames.from_list(
            self.parameters.channel_names
        )

    def got_valid_key_for(self, channel):
        # TODO based on self.parameters.get_key_for_channel_name and channel
        return True

    def no_such_channel_message(self, channel_name):
        return [ERR_NOSUCHCHANNEL(channel_name, self.actor)]

    def invalid_key_message(self, channel):
        # TODO
        return []

    def join_message(self, channel):
        ret = [
            M(ActorCollection(channel.users), 'JOIN', str(channel), prefix=self.user),
            RPL_NAMEREPLY(self.actor, channel),
            RPL_ENDOFNAMES(self.actor)
        ]
        if channel.topic is not None:
            ret.append(RPL_TOPIC(self.actor, channel))
        return ret

    @staticmethod
    def get_channel(channel_name):
        if Channel.exists(channel_name):
            channel = Channel.get(channel_name)
        else:
            channel = Channel(channel_name)
            channel.save()
        return channel

