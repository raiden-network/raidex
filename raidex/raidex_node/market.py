from raiden.utils import isaddress, make_address
from ethereum.utils import privtoaddr, sha3

from raidex.raidex_node.offer_book import OfferType
from raidex.utils import pex


class TokenPair(object):

    def __init__(self, base_token, counter_token):
        if not isaddress(base_token) or not isaddress(counter_token):
            raise ValueError("base_token and counter_token must be valid addresses")
        self.base_token = base_token
        self.counter_token = counter_token

    @classmethod
    def random(cls):
        base_token = make_address()
        counter_token = make_address()
        return cls(base_token, counter_token)

    @classmethod
    def from_seed(cls, seed):
        return cls(privtoaddr(sha3(seed)), privtoaddr(sha3(seed+seed)))

    def opposite(self):
        return TokenPair(base_token=self.counter_token, counter_token=self.base_token)

    def get_offer_type(self, ask_token, bid_token):
        if ask_token == self.base_token and bid_token == self.counter_token:
            return OfferType.BUY
        elif ask_token == self.counter_token and bid_token == self.base_token:
            return OfferType.SELL
        else:
            return None

    def __eq__(self, other):
        return self.base_token == other.base_token and self.counter_token == other.counter_token

    def __repr__(self):
        return "TokenPair<base={}, counter={}".format(pex(self.base_token), pex(self.counter_token))



