import structlog

from raidex.raidex_node.architecture.state_change import *
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.transport.events import SendProvenCommitmentEvent
from raidex.raidex_node.matching.match import MatchFactory
from raidex.raidex_node.architecture.data_manager import DataManager
from raidex.utils.greenlet_helper import future_timeout
from raidex.constants import OFFER_THRESHOLD_TIME


logger = structlog.get_logger('StateChangeHandler')


def handle_state_change(raidex_node, state_change):

    data_manager = raidex_node.data_manager

    if isinstance(state_change, OfferStateChange):
        handle_offer_state_change(data_manager, state_change)
    if isinstance(state_change, OfferTimeoutStateChange):
        handle_offer_timeout(data_manager, state_change)
    if isinstance(state_change, NewLimitOrderStateChange):
        handle_new_limit_order(data_manager, state_change)
    if isinstance(state_change, OfferPublishedStateChange):
        handle_offer_published(data_manager, state_change)
    if isinstance(state_change, ProvenCommitmentStateChange):
        handle_proven_commitment(data_manager, state_change)
    if isinstance(state_change, TransferReceivedStateChange):
        handle_transfer_received(data_manager, state_change)


def handle_offer_state_change(data_manager: DataManager, state_change: OfferStateChange):
    offer = data_manager.offer_manager.get_offer(state_change.offer_id)

    if isinstance(state_change, CommitmentProofStateChange):
        handle_commitment_proof(data_manager, offer, state_change)
    if isinstance(state_change, PaymentFailedStateChange):
        offer.payment_failed()
        logger.info(f'Offer Payment Failed: {offer.offer_id}')


def handle_offer_timeout(data_manager: DataManager, state_change: OfferTimeoutStateChange):
    if data_manager.offer_manager.has_offer(state_change.offer_id):
        offer = data_manager.offer_manager.get_offer(state_change.offer_id)
        offer.timeout()
        logger.info(f'Offer timeout: {offer.offer_id}, timeout at: {state_change.timeout_date}')
    elif data_manager.matching_engine.offer_book.contains(state_change.offer_id):
        data_manager.matching_engine.offer_book.remove_offer(state_change.offer_id)

    data_manager.timeout_handler.clean_up_timeout(state_change.offer_id)


def handle_new_limit_order(data_manager: DataManager, state_change: NewLimitOrderStateChange):
    new_order = LimitOrder.from_dict(state_change.data)
    data_manager.process_order(new_order)


def handle_offer_published(data_manager: DataManager, event: OfferPublishedStateChange):
    offer_book_entry = event.offer_entry
    offer_id = offer_book_entry.offer.offer_id

    if data_manager.offer_manager.has_offer(offer_id):
        offer = data_manager.offer_manager.get_offer(offer_id)
        offer.received_offer()
    else:
        data_manager.matching_engine.offer_book.insert_offer(offer_book_entry)
        data_manager.timeout_handler.create_new_timeout(offer_book_entry.offer, OFFER_THRESHOLD_TIME)


def handle_commitment_proof(data_manager: DataManager, offer, state_change: CommitmentProofStateChange):
    commitment_proof = state_change.commitment_proof
    commitment_signature = state_change.commitment_signature

    offer.receive_commitment_proof(commitment_proof)

    if offer.offer_id in data_manager.matches:
        match = data_manager.matches[offer.offer_id]
        match.matched()
        dispatch_events([SendProvenCommitmentEvent(match.target, offer)])

    logger.info(f'Received Commitment Proof: {offer.offer_id}')


def handle_proven_commitment(data_manager: DataManager, state_change: ProvenCommitmentStateChange):

    offer_id = state_change.commitment.offer_id
    offer = data_manager.offer_manager.get_offer(offer_id)

    match = MatchFactory.maker_match(offer, state_change.commitment, state_change.commitment_proof)
    data_manager.matches[offer_id] = match
    match.matched()


def handle_transfer_received(data_manager: DataManager, state_change: TransferReceivedStateChange):

    offer_id = state_change.raiden_event.identifier

    match = data_manager.matches[offer_id]
    match.received_inbound(state_change.raiden_event)
    # TODO This is wrong here timeout handling scheme not finished yet
    data_manager.timeout_handler.clean_up_timeout(offer_id)


