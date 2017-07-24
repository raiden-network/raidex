from gevent.queue import PriorityQueue

from raidex.raidex_node.trader.trader import TransferReceipt
from raidex.commitment_service.refund import Refund


def test_priority():
    refund_queue = PriorityQueue()
    receipt = TransferReceipt(sender=123, amount=1, identifier=123, received_timestamp=1)

    # higher priority
    refund1 = Refund(receipt, priority=1, claim_fee=False)
    # lower priority
    refund2 = Refund(receipt, priority=5, claim_fee=False)

    assert refund1 > refund2

    refund_queue.put(refund1)
    refund_queue.put(refund2)

    received_first = refund_queue.get()
    received_second = refund_queue.get()

    assert received_first == refund2
    assert received_second == refund1

