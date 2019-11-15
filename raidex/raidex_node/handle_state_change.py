import structlog

from raidex.raidex_node.architecture.state_change import *
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.transport.events import SendProvenOfferEvent
from raidex.raidex_node.matching.match import MatchFactory
from raidex.raidex_node.architecture.data_manager import DataManager
from raidex.constants import OFFER_THRESHOLD_TIME
from raidex.raidex_node.trader.events import MakeChannelEvent
from raidex.raidex_node.raidex_node import RaidexNode


logger = structlog.get_logger('StateChangeHandler')


def handle_state_change(raidex_node, state_change):

    data_manager = raidex_node.data_manager

    if isinstance(state_change, OfferStateChange):
        handle_offer_state_change(data_manager, state_change)
    if isinstance(state_change, OfferTimeoutStateChange):
        handle_offer_timeout(data_manager, state_change)
    if isinstance(state_change, NewLimitOrderStateChange):
        handle_new_limit_order(data_manager, state_change)
    if isinstance(state_change, CancelLimitOrderStateChange):
        handle_cancel_limit_order(data_manager, state_change)
    if isinstance(state_change, OfferPublishedStateChange):
        handle_offer_published(data_manager, state_change)
    if isinstance(state_change, TakerCallStateChange):
        handle_taker_call(data_manager, state_change)
    if isinstance(state_change, TransferReceivedStateChange):
        handle_transfer_received(data_manager, state_change)
    if isinstance(state_change, ChannelStatusStateChange):
        handle_channel_status_update(raidex_node, state_change)
    if isinstance(state_change, MakeChannelStateChange):
        handle_make_channel(state_change)


def handle_offer_state_change(data_manager: DataManager, state_change: OfferStateChange):
    offer = data_manager.offer_manager.get_offer(state_change.offer_id)

    if isinstance(state_change, CommitmentProofStateChange):
        handle_commitment_proof(data_manager, offer, state_change)
    if isinstance(state_change, PaymentFailedStateChange):
        offer.payment_failed()
        logger.info(f'Offer Payment Failed: {offer.offer_id}')
    if isinstance(state_change, CancellationProofStateChange):
        handle_cancellation_proof(offer, state_change)


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


def handle_cancel_limit_order(data_manager: DataManager, state_change: CancelLimitOrderStateChange):
    order_id = state_change.data['order_id']
    data_manager.cancel_order(order_id)


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

    offer.receive_commitment_proof(proof=commitment_proof)
    message_target = None

    if offer.offer_id in data_manager.matches:
        match = data_manager.matches[offer.offer_id]
        match.matched()
        message_target = match.target

    dispatch_events([SendProvenOfferEvent(offer, data_manager.market, message_target)])

    logger.info(f'Received Commitment Proof: {offer.offer_id}')


def handle_cancellation_proof(offer, state_change: CancellationProofStateChange):
    cancellation_proof = state_change.cancellation_proof

    offer.receive_cancellation_proof(cancellation_proof)


def handle_taker_call(data_manager: DataManager, state_change: TakerCallStateChange):

    offer_id = state_change.offer_id
    offer = data_manager.offer_manager.get_offer(offer_id)

    match = MatchFactory.maker_match(offer, state_change.initiator, state_change.commitment_proof)
    data_manager.matches[offer_id] = match
    match.matched()


def handle_transfer_received(data_manager: DataManager, state_change: TransferReceivedStateChange):

    offer_id = state_change.raiden_event.identifier

    match = data_manager.matches[offer_id]
    match.received_inbound(raiden_event=state_change.raiden_event)

    if match.offer.state == 'completed':
        data_manager.timeout_handler.clean_up_timeout(offer_id)
        from raidex.raidex_node.order import fsm_offer
        fsm_offer.remove_model(match.offer)


def handle_channel_status_update(raidex_node: RaidexNode, state_change: ChannelStatusStateChange):
    raidex_node.raiden_info.set_channels(state_change.channel_raw_data)


def handle_make_channel(state_change):

    make_channel_event = MakeChannelEvent(
        partner_address=state_change.data['partner_address'],
        token_address=state_change.data['token_address'],
        total_deposit=state_change.data['total_deposit']
    )

    print(make_channel_event)
    dispatch_events([make_channel_event])
