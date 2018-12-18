import structlog
from gevent.queue import PriorityQueue

from raidex.raidex_node.trader.trader import TraderClientMock
from raidex.signing import Signer
from raidex.commitment_service.tasks import (
    RefundTask,
    MessageSenderTask,
    MakerCommitmentTask,
    TakerCommitmentTask,
    SwapExecutionTask,
    TransferReceivedTask
)

log = slogging.get_logger('commitment_service')
log_swaps = slogging.get_logger('commitment_service.asset_swaps')
log_messaging = slogging.get_logger('commitment_service.messaging')
log_refunds = slogging.get_logger('commitment_service.refunds')
log_trader = slogging.get_logger('commitment_service.trader')


class RaidexException(Exception):
    pass


class CommitmentTaken(RaidexException):
    pass


class CommitmentMismatch(RaidexException):
    pass


class CommitmentService(object):

    def __init__(self, signer, message_broker, trader_client, fee_rate=None):
        self._sign = signer.sign
        self.address = signer.address
        self.swaps = dict()  # offer_hash -> CommitmentTuple
        self.trader_client = trader_client
        # FIXME fee_rate should be int representation (int(float_rate/uint32.max_int)) for CSAdvertisements
        self.fee_rate = fee_rate
        self.message_broker = message_broker
        self.refund_queue = PriorityQueue()  # type: (TransferReceipt, substract_fee <bool>)
        self.message_queue = PriorityQueue()  # type: (messages.Signed, recipient (str) or None)

    def start(self):
        self.trader_client.start()
        MakerCommitmentTask(self.swaps, self.refund_queue, self.message_queue, self.message_broker, self.address).start()
        TakerCommitmentTask(self.swaps, self.message_broker, self.address).start()
        SwapExecutionTask(self.swaps, self.message_broker, self.address).start()
        TransferReceivedTask(self.swaps, self.trader_client).start()
        RefundTask(self.trader_client, self.refund_queue, self.fee_rate).start()
        MessageSenderTask(self.message_broker, self.message_queue, self._sign).start()

    @classmethod
    def build_from_mock(cls, privkey_seed, message_broker, trader, fee_rate=None):
        signer = Signer.from_seed(privkey_seed)
        message_broker_client = message_broker
        trader_client = TraderClientMock(signer.address, commitment_balance=0, trader=trader)

        return cls(signer, message_broker_client, trader_client, fee_rate)
