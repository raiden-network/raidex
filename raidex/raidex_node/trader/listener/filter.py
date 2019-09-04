from raidex.raidex_node.trader.listener.events import PaymentReceivedEvent, ChannelStatusRaidenEvent
from raidex.raidex_node.architecture.state_change import TransferReceivedStateChange, ChannelStatusStateChange
from raidex.raidex_node.architecture.filter import Filter


class RaidenEventFilter(Filter):
    def _filter(self, event):
        raise NotImplementedError

    def _transform(self, event):
        raise NotImplementedError

    def removable(self):
        raise NotImplementedError


class TransferReceivedFilter(RaidenEventFilter):

    def __init__(self, initiator, identifier):
        self.initiator = initiator
        self.identifier = identifier

    def _filter(self, event):
        if not isinstance(event, PaymentReceivedEvent):
            return False
        if event.initiator != self.initiator:
            return False
        if event.identifier != self.identifier:
            return False
        return True

    def _transform(self, event: PaymentReceivedEvent):
        return TransferReceivedStateChange(event)

    def removable(self):
        return True


class ChannelFilter(RaidenEventFilter):

    def __init__(self, channel_data_raw):
        self.channel_data_raw = channel_data_raw

    def _filter(self, event):
        if not isinstance(event, ChannelStatusRaidenEvent):
            return False
        # TODO Filter if there are no changes
        return True

    def _transform(self, event: ChannelStatusRaidenEvent):
        return ChannelStatusStateChange(event.channel_data)

    def removable(self):
        return True
