import rlp
from rlp.sedes import binary
from ethereum.utils import (address, int256, hash32, sha3, big_endian_to_int)
from raiden.utils import pex
from raiden.encoding.signing import recover_publickey, GLOBAL_CTX
from raiden.encoding.signing import sign as _sign
from secp256k1 import PrivateKey, ALL_FLAGS

from rex.utils import milliseconds

sig65 = binary.fixed_length(65)


def sign(messagedata, private_key):
    if not isinstance(private_key, PrivateKey):
        privkey_instance = PrivateKey(privkey=private_key, flags=ALL_FLAGS, ctx=GLOBAL_CTX)
    else:
        privkey_instance = private_key
    return _sign(messagedata, privkey_instance)


class RLPHashable(rlp.Serializable):
    # _cached_rlp caches serialized object

    @property
    def hash(self):
        return sha3(rlp.encode(self, cache=True))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __hash__(self):
        return big_endian_to_int(self.hash)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        try:
            h = self.hash
        except Exception:
            h = ''
        return '<%s(%s)>' % (self.__class__.__name__, pex(h))


class SignatureMissingError(Exception):
    pass


class Signed(RLPHashable):

    _sender = ''
    signature = ''
    fields = [('signature', sig65)]

    # def __init__(self, sender=''):
    #     assert not sender or isaddress(sender)
    #     super(Signed, self).__init__(sender=sender)

    def __len__(self):
        return len(rlp.encode(self))

    @property
    def _hash_without_signature(self):
        return sha3(rlp.encode(self, self.exclude(['signature'])))

    def sign(self, privkey):
        assert self.is_mutable()
        assert isinstance(privkey, bytes) and len(privkey) == 32
        self.signature = sign(self._hash_without_signature, privkey)
        self.make_immutable()
        return self

    @property
    def sender(self):
        if not self._sender:
            if not self.signature:
                raise SignatureMissingError()
            pub = recover_publickey(self._hash_without_signature, self.signature)
            self._sender = sha3(pub[1:])[-20:]
        return self._sender


class Offer(Signed):

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

    def timed_out(self, at=None):
        if at is None:
            at = milliseconds.time_int()
        return self.timeout < at

    def __repr__(self):
        try:
            h = self.hash
        except Exception:
            h = ''
        try:
            sender = self.sender
        except SignatureMissingError:
            sender = ''
        return '<%s(%s) ask: %s[%s] bid %s[%s] h:%s sender:%s>' % (
            self.__class__.__name__,
            pex(self.offer_id),
            pex(self.ask_token),
            self.ask_amount,
            pex(self.bid_token),
            self.bid_amount,
            pex(h),
            pex(sender)
        )


class Commitment(Signed):

    fields = [
        ('offer_id', hash32),
        ('timeout', int256),
        ('amount', int256),
    ]

    def __init__(self, offer_id, timeout, amount):
        super(Commitment, self).__init__(offer_id, timeout, amount)


class CommitmentProof(Signed):

    fields = [
        ('commitment_sig', sig65)
    ]

    def __init__(self, commitment_sig):
        super(CommitmentProof, self).__init__(commitment_sig)


class ProvenOffer(Signed):

    fields = [
        ('offer', Offer),
        ('commitment', Commitment),
        ('commitment_proof', CommitmentProof),
    ]

    def __init__(self, offer, commitment, commitment_proof):
        super(ProvenOffer, self).__init__(offer, commitment, commitment_proof)
