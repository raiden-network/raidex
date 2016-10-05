import rlp
from ethereum.utils import address, int256, hash32


class Offer(rlp.Serializable):

    fields = [
        ('ask_token', address),
        ('ask_amount', int256),
        ('bid_token', address),
        ('bid_amount', int256),
        ('offer_id', hash32),
        ('timeout', int256),
    ]

    def __init__(self, ask_token, ask_amount,
                 bid_token, bid_amount,
                 offer_id, timeout):
        super(Offer, self).__init__(ask_token, ask_amount,
                 bid_token, bid_amount, offer_id, timeout)
