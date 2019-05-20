import structlog

from raidex.raidex_node.architecture.state_change import *
from raidex.raidex_node.order.limit_order import LimitOrder

logger = structlog.get_logger('StateChangeHandler')


def handle_state_change(raidex_node, state_change):

    data_manager = raidex_node.data_manager

    if isinstance(state_change, OfferStateChange):
        handle_offer_state_change(data_manager, state_change)
    if isinstance(state_change, NewLimitOrderStateChange):
        handle_new_limit_order(data_manager, state_change)
    if isinstance(state_change, OfferPublishedStateChange):
        handle_offer_published(data_manager, state_change)


def handle_offer_state_change(data_manager, state_change: OfferStateChange):
    offer = data_manager.offer_manager.get_offer(state_change.offer_id)

    if isinstance(state_change, OfferTimeoutStateChange):
        offer.timeout()
        logger.info(f'Offer timeout: {offer.offer_id}, timeout at: {state_change.timeout_date}')
    if isinstance(state_change, CommitmentProofStateChange):
        handle_commitment_proof(data_manager, offer, state_change)

    if isinstance(state_change, PaymentFailedStateChange):
        offer.payment_failed()
        logger.info(f'Offer Payment Failed: {offer.offer_id}')


def handle_new_limit_order(data_manager, state_change: NewLimitOrderStateChange):
    new_order = LimitOrder.from_dict(state_change.data)
    data_manager.process_order(new_order)


def handle_offer_published(data_manager, event: OfferPublishedStateChange):
    offer_data = event.offer

    if data_manager.offer_manager.has_offer(offer_data.offer_id):
        offer = data_manager.offer_manager.get_offer(offer_data.offer_id)
        offer.received_offer()
    else:
        data_manager.matching_engine.offer_book.insert_offer(offer_data)


def handle_commitment_proof(data_manager, offer, state_change: CommitmentProofStateChange):
    commitment_proof = state_change.commitment_proof
    commitment_signature = state_change.commitment_signature

    offer.receive_commitment_proof(commitment_proof)

    if offer.offer_id in data_manager.matches:
        match = data_manager.matches[offer.offer_id]
        match.matched()

    logger.info(f'Received Commitment Proof: {offer.offer_id}')