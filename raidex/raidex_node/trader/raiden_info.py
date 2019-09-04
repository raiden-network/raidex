from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.trader.listener.events import ChannelFilterEvent


class RaidenInfo:

    def __init__(self):
        self.channels = {}

    def get_channels(self):
        return self.channels

    def set_channels(self, channels_raw_data):
        self.channels = channels_raw_data
        dispatch_events([ChannelFilterEvent(self.channels)])

    def start(self):
        dispatch_events([ChannelFilterEvent(self.channels)])

