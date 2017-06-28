import random
import string
from ethereum.utils import sha3, privtoaddr


def generate_random_privkey():
    return sha3(''.join(random.choice(string.printable) for _ in range(20)))


class Signer(object):

    def __init__(self, private_key):
        self._private_key = private_key
        self._address = privtoaddr(private_key)

    @classmethod
    def random(cls):
        private_key = generate_random_privkey()
        return cls(private_key)

    @property
    def address(self):
        return self._address

    def sign(self, message):
        message.sign(self._private_key)
