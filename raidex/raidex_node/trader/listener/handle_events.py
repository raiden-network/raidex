from raidex.raidex_node.trader.listener.events import *
from raidex.raidex_node.trader.listener.filter import TransferReceivedFilter, ChannelFilter


def handle_event(raiden_listener, event):

    if isinstance(event, RaidenEvent):
        raiden_listener.new_raiden_event(event)

    if isinstance(event, ExpectInboundEvent):
        new_listener = TransferReceivedFilter(event.initiator, event.identifier)
        raiden_listener.add_event_filter(new_listener)

    if isinstance(event, ChannelFilterEvent):
        new_listener = ChannelFilter(event.channel_data_raw)
        raiden_listener.add_event_filter(new_listener)
