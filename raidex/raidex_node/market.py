from eth_utils import keccak, decode_hex, is_binary_address, to_checksum_address
from eth_keys import keys
from raidex.raidex_node.order.offer import OfferType
from raidex.utils import pex, make_address


class TokenPair(object):

    def __init__(self, base_token, base_decimal=3, quote_token=b'', quote_decimal=18):

        if not is_binary_address(base_token) or not is_binary_address(quote_token):
            raise ValueError("base_token and quote_token must be valid addresses")
        self.base_token = base_token
        self.base_decimal = base_decimal
        self.quote_token = quote_token
        self.quote_decimal = quote_decimal

    @classmethod
    def random(cls):
        base_token = make_address()
        quote_token = make_address()
        return cls(base_token, quote_token)

    @classmethod
    def from_seed(cls, seed):
        private_key_base = keys.PrivateKey(keccak(text=seed))
        private_key_quote = keys.PrivateKey(keccak(text=(seed+seed)))
        public_key_base = private_key_base.public_key
        public_key_quote = private_key_quote.public_key

        return cls(decode_hex(public_key_base.to_address()), decode_hex(public_key_quote.to_address()))

    def opposite(self):
        return TokenPair(base_token=self.quote_token,
                         base_decimal=self.quote_decimal,
                         quote_token=self.base_token,
                         quote_decimal=self.base_decimal)

    def get_offer_type(self, ask_token, bid_token):
        if ask_token == self.base_token and bid_token == self.quote_token:
            return OfferType.BUY
        elif ask_token == self.quote_token and bid_token == self.base_token:
            return OfferType.SELL
        else:
            return None

    @property
    def checksum_base_address(self):
        return to_checksum_address(self.base_token)

    @property
    def checksum_quote_address(self):
        return to_checksum_address(self.quote_token)

    def __eq__(self, other):
        return self.base_token == other.base_token and self.quote_token == other.quote_token

    def __repr__(self):
        return "TokenPair<base={}, quote={}".format(pex(self.base_token), pex(self.quote_token))



