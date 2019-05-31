from raidex.raidex_node.transport.events import *


def handle_event(transport, event):

    if isinstance(event, (SendMessageEvent, BroadcastEvent)):
        transport.send_message(event.topic, event.message)

    if isinstance(event, SendProvenCommitmentEvent):
        transport.proven_offer(event.target, event.offer, event.offer.proof)

    if isinstance(event, CancellationEvent):
        transport.cancellation(event.target, event.offer_id)