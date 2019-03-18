import random
import string
from eth_utils import keccak, decode_hex, encode_hex
from eth_keys import keys
from raidex.account import Account


def generate_random_privkey():
    return keccak(''.join(random.choice(string.printable) for _ in range(20)))


class Signer(object):

    def __init__(self, private_key):
        self._private_key = private_key
        self._address = keys.PrivateKey(private_key).public_key

    @classmethod
    def random(cls):
        private_key = generate_random_privkey()
        return cls(private_key)

    @classmethod
    def from_seed(cls, seed):
        private_key = keccak(text=seed)
        return cls(private_key)

    @classmethod
    def from_account(cls, account: Account):
        private_key = account.privkey
        return cls(private_key)

    @property
    def address(self):
        return decode_hex(self._address.to_address())

    @property
    def canonical_address(self) -> str:
        return self._address.to_canonical_address()

    @property
    def checksum_address(self) -> str:
        return self._address.to_checksum_address()

    def sign(self, message):
        message.sign(self._private_key)

    def __repr__(self):
        return '<{}, {}>'.format(self.__class__.__name__, encode_hex(self.address))