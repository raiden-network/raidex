class Refund(object):

    def __init__(self, receipt, priority, claim_fee):
        # type: (TransferReceipt, int, bool) -> None
        assert type(claim_fee) is bool
        self.receipt = receipt
        self.priority = priority
        self.claim_fee = claim_fee

    def __cmp__(self, other):
        # compare the whole object easily for the Priority-Queue ordering.
        # Higher priority means it will get refunded earlier
        if self.priority < other.priority:
            # lower priority: self > other:
            return 1
        if self.priority > other.priority:
            # higher priority: self < other
            return -1
        return 0