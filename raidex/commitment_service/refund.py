from functools import total_ordering



@total_ordering
class Refund(object):

    def __init__(self, receipt, priority, claim_fee):
        # type: (TransferReceipt, int, bool) -> None
        assert type(claim_fee) is bool
        self.receipt = receipt
        self.priority = priority
        self.claim_fee = claim_fee

    def __eq__(self, other):
        if self.priority == other.priority:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        # greater number means lower priority
        return self.priority > other.priority

    # def __cmp__(self, other):
    #    # compare the whole object easily for the Priority-Queue ordering.
    #    # Higher priority means it will get refunded earlier
    #    if self.priority < other.priority:
    #        # lower priority: self > other:
    #        return 1
    #    if self.priority > other.priority:
    #        # higher priority: self < other
    #        return -1
    #    return 0

    def __repr__(self):
        return "{}<receipt={}, claim_fee={}>".format(
            self.__class__.__name__,
            self.receipt,
            self.claim_fee,
        )
