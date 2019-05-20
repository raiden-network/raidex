from raidex.raidex_node.transport.events import *


def handle_event(message_broker_client, event):

    if isinstance(event, (SendMessageEvent, BroadcastEvent)):
        message_broker_client.send(event.topic, event.message)