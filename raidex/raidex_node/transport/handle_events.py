from raidex.raidex_node.transport.events import *
from raidex.raidex_node.transport.transport import Transport


def handle_event(transport: Transport, event: TransportEvent):

    if isinstance(event, SignMessageEvent) and isinstance(event, SendMessageEvent):
        transport.sign_message(event.message)

    if isinstance(event, (SendMessageEvent, BroadcastEvent)):
        transport.send_message(event)