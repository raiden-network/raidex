import structlog

from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.transport.events import CancellationEvent, CommitmentEvent, SendExecutedEventEvent
from raidex.raidex_node.commitment_service.events import CommitmentServiceEvent
from raidex.raidex_node.architecture.event_architecture import Processor
from raidex.raidex_node.commitment_service.tasks import CommitmentProofTask
from raidex.message_broker.listeners import CommitmentProofListener
from raidex.raidex_node.trader.events import TransferEvent
from raidex.raidex_node.trader.listener.events import ExpectInboundEvent
from raidex.utils.address import binary_address
from raidex.raidex_node.order.offer import Offer
from raidex.constants import FEE_ADDRESS, COMMITMENT_AMOUNT


log = structlog.get_logger('node.commitment_service')


class OfferIdentifierCollision(Exception):
    pass


class MessageBrokerConnectionError(Exception):
    pass


class CommitmentServiceClient(Processor):
    """
    Interactions concerning the Commitment for Offers (maker) and ProvenOffers (taker).
    Handles the Commitment-Transfers in the Trader and the communication with the CS (Message-Broker)
    Methods will return the proper confirmation-messages of commitments (ProvenOffer/maker, ProvenCommitment/taker)
    """

    def __init__(self, signer, market, message_broker, commitment_service_address, fee_rate):
        super(CommitmentServiceClient, self).__init__(CommitmentServiceEvent)
        self.node_address = signer.checksum_address
        self.commitment_service_address = binary_address(commitment_service_address)
        self.fee_rate = fee_rate
        self.message_broker = message_broker
        self.commitment_amount = COMMITMENT_AMOUNT
        self.market = market

        CommitmentProofTask(CommitmentProofListener(self.message_broker, topic=self.node_address)).start()

    def commit(self, offer: Offer):

        commit_msg_event = CommitmentEvent(self.commitment_service_address, offer, self.commitment_amount, self.market)
        transfer_event = self._transfer_commitment_event(offer.offer_id, self.commitment_amount)
        dispatch_events([commit_msg_event, transfer_event])

    def received_inbound_from_swap(self, offer_id):
        # type: (int) -> None
        swap_execution_event = SendExecutedEventEvent(self.commitment_service_address, offer_id)
        dispatch_events([swap_execution_event, ExpectInboundEvent(self.commitment_service_address, offer_id)])

    def request_cancellation(self, offer: Offer):
        cancellation_request_event = CancellationEvent(self.commitment_service_address, offer.offer_id)
        dispatch_events([cancellation_request_event])

    def _transfer_commitment_event(self, offer_id, commitment_amount):
        return TransferEvent(FEE_ADDRESS,
                             self.commitment_service_address,
                             commitment_amount,
                             offer_id)

