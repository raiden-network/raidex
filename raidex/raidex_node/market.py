from eth_utils import keccak, decode_hex, is_binary_address, to_checksum_address
from eth_keys import keys
from raidex.raidex_node.offer_book import OfferType
from raidex.utils import pex, make_address


class TokenPair(object):

    def __init__(self, base_token, counter_token):

        if not is_binary_address(base_token) or not is_binary_address(counter_token):
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
        private_key_base = keys.PrivateKey(keccak(text=seed))
        private_key_counter = keys.PrivateKey(keccak(text=(seed+seed)))
        public_key_base = private_key_base.public_key
        public_key_counter = private_key_counter.public_key

        return cls(decode_hex(public_key_base.to_address()), decode_hex(public_key_counter.to_address()))

    def opposite(self):
        return TokenPair(base_token=self.counter_token, counter_token=self.base_token)

    def get_offer_type(self, ask_token, bid_token):
        if ask_token == self.base_token and bid_token == self.counter_token:
            return OfferType.BUY
        elif ask_token == self.counter_token and bid_token == self.base_token:
            return OfferType.SELL
        else:
            return None

    def checksum_base_address(self):
        return to_checksum_address(self.base_token)

    def checksum_counter_address(self):
        return to_checksum_address(self.counter_token)

    def __eq__(self, other):
        return self.base_token == other.base_token and self.counter_token == other.counter_token

    def __repr__(self):
        return "TokenPair<base={}, counter={}".format(pex(self.base_token), pex(self.counter_token))



