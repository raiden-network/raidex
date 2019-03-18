import structlog
from gevent.queue import PriorityQueue

from raidex.raidex_node.trader.client import TraderClient
from raidex.account import Account
from raidex.signing import Signer
from raidex.commitment_service.tasks import (
    RefundTask,
    MessageSenderTask,
    MakerCommitmentTask,
    TakerCommitmentTask,
    SwapExecutionTask,
    TransferReceivedTask
)

from eth_utils import to_checksum_address

CS_MOCK_KEYFILE='/home/fred/fred/work/brainbot/raidex/keystore/charlie-cs'
CS_MOCK_PW_FILE='/home/fred/fred/work/brainbot/raidex/keystore/pw/pw'
KOVAN_RTT_ADDRESS = '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb'

log = structlog.get_logger('commitment_service')
log_swaps = structlog.get_logger('commitment_service.asset_swaps')
log_messaging = structlog.get_logger('commitment_service.messaging')
log_refunds = structlog.get_logger('commitment_service.refunds')
log_trader = structlog.get_logger('commitment_service.trader')


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
        RefundTask(self.trader_client, self.refund_queue, KOVAN_RTT_ADDRESS, self.fee_rate).start()
        MessageSenderTask(self.message_broker, self.message_queue, self._sign).start()

    @property
    def checksum_address(self):
        return to_checksum_address(self.address)

    @classmethod
    def build_from_mock(cls, message_broker, fee_rate=None):

        pw = open(CS_MOCK_PW_FILE, 'r').read()
        if pw != '':
            pw = pw.splitlines()[0]
        acc = Account.load(path=CS_MOCK_KEYFILE, password=pw)
        signer = Signer.from_account(acc)
        message_broker_client = message_broker
        trader_client = TraderClient(signer.canonical_address, host='localhost', port=5003, api_version='v1', commitment_amount=10)

        return cls(signer, message_broker_client, trader_client, fee_rate)
