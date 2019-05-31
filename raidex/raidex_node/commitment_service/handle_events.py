from gevent import spawn

from raidex.raidex_node.commitment_service.client import CommitmentServiceClient
from raidex.raidex_node.commitment_service.events import *
from raidex.message_broker.listeners import TakerListener, listener_context
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes
from raidex.raidex_node.architecture.state_change import ProvenCommitmentStateChange


def handle_event(commitment_service: CommitmentServiceClient, event):
    if isinstance(event, CommitEvent):
        if event.offer.is_maker():
            commitment_service.maker_commit(event.offer)
        else:
            commitment_service.taker_commit(event.offer)
    if isinstance(event, CommitmentProvedEvent):
        spawn(wait_for_taker, event, commitment_service.message_broker)
    if isinstance(event, ReceivedInboundEvent):
        commitment_service.report_swap_executed(event.offer.offer_id)
    if isinstance(event, CancellationRequestEvent):
        commitment_service.request_cancellation(event.offer)


def wait_for_taker(event, message_broker):
    with listener_context(TakerListener(event.offer, message_broker)) as taker_listener:
        print(f'WAIT FOR TAKER')
        proven_commitment = taker_listener.get()
        print(f'TAKER_ADDRESS: {proven_commitment}')
        proven_commitment_state_change = ProvenCommitmentStateChange(proven_commitment.commitment,
                                                                     proven_commitment.commitment_proof)
        dispatch_state_changes(proven_commitment_state_change)