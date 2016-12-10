import json
import base64

import rlp
from rlp.sedes import binary
from ethereum.utils import (address, int256, hash32, sha3, big_endian_to_int, int32)
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

class Ping(Signed):

    fields = [
        ('nonce', int256)
    ]

    def __init__(self, nonce):
        super(Ping, self).__init__(nonce)


class Offer(Signed):
    """An `Offer` is the base for a `ProvenOffer`. It's `offer_id`, `hash` and `timeout` should be sent
    as a `Commitment` to a commitment service provider.

    Data:
        offer = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id, timeout])
        timeout = <UTC milliseconds since epoch>
        offer_sig = sign(sha3(offer), maker)

    Broadcast:
        {
            "msg": "offer",
            "version": 1,
            "data": "rlp([offer])"
        }
    """

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
    """A `Commitment` announces the commitment service, that a maker or taker wants to engage in the
    offer with the `offer_id`. `offer_hash`, `timeout` should match the later published `Offer`; the
    `amount` is the amount of tokens that will be sent via `raiden` in a following transfer.

    Process note: the raiden transfer to fulfill the commitment should use the `offer_id` as an identifier.

    Data:
        offer_id = offer_id
        offer_hash = sha3(offer)
        timeout = int256 <unix timestamp (ms) for the end of the offers validity>
        amount = int256 <value of tokens in the commitment-service's commitment currency>

    Broadcast:
        {
            "msg": "commitment",
            "version": 1,
            "data": rlp([offer_id, offer_hash, timeout, amount])
        }
    """

    fields = [
        ('offer_id', hash32),
        ('offer_hash', hash32),
        ('timeout', int256),
        ('amount', int256),
    ]

    def __init__(self, offer_id, offer_hash, timeout, amount):
        super(Commitment, self).__init__(offer_id, offer_hash, timeout, amount)


class CommitmentProof(Signed):
    """A `CommitmentProof` is the commitment service's signature that a commitment was made. It allows
    maker and taker to confirm each other's commitment to the swap.

    Data:
        commitment_sig = sign(commitment, cs)

    Broadcast:
        {
            "msg": "commitment_proof",
            "version": 1,
            "data": rlp(commitment.signature)
        }
    """

    fields = [
        ('commitment_sig', sig65)
    ]

    def __init__(self, commitment_sig):
        super(CommitmentProof, self).__init__(commitment_sig)


class ProvenOffer(Signed):
    """A `ProvenOffer` is published by a market maker and pushed to one ore more broadcast services.
    A taker should recover the commitment service address from the `commitment_proof` and commit to it, if
    they want to engage in the swap.

    Data:
        offer = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id, timeout])
        timeout = <UTC milliseconds since epoch>
        offer_sig = sign(sha3(offer), maker)
        commitment = rlp([offer_id, sha3(offer), timeout, amount])
        commitment_sig = raiden signature of the commitment transfer by the committer
        commitment_proof = sign(commitment_sig, cs)

    Broadcast:
        {
            "msg": "offer",
            "version": 1,
            "data": "rlp([offer, commitment, commitment_proof])"
        }
    """
    fields = [
        ('offer', Offer),
        ('commitment', Commitment),
        ('commitment_proof', CommitmentProof),
    ]

    def __init__(self, offer, commitment, commitment_proof):
        super(ProvenOffer, self).__init__(offer, commitment, commitment_proof)


class CommitmentServiceAdvertisement(Signed):
    """A `CommitmentServiceAdvertisement` can be send by the Commitment Service (CS) to broadcast services
    in order to announce its service to users.

    Data:
        address = <ethereum/raiden address>
        commitment_asset = <asset_address of the accepted commitment currency>
        fee_rate = <uint32 (fraction of uint32.max_int)>

    Broadcast:
        {
            "msg": "commitment_service",
            "data": rlp([address, commitment_asset, fee_rate]),
            "version": 1
        }

    Fee calculations:

    Users of the service have to expect to have a fee of e.g.

    uint32_maxint = 2 ** 32
    fee = int(float_fee_rate/uint32_maxint * commitment_in_wei + .5)

    mock fee: random.randint(1, 100000) # wei
    mock fee_rate: int(random.random() * uint32_maxint)

    deducted from each commitment.
    """

    fields = [
        ('address', address),
        ('commitment_asset', address),
        ('fee_rate', int32),
    ]

    def __init__(self, address, commitment_asset, fee_rate):
        super(CommitmentServiceAdvertisement, self).__init__(address, commitment_asset, fee_rate)


class SwapExecution(Signed):
    """`SwapExecution` is used by both parties of a swap, in order to confirm to the CS that the swap
    went through and have the committed tokens released.

    Data:
        offer_id = offer.offer_id
        timestamp = int256 <unix timestamp (ms) of the successful execution of the swap>

    Broadcast:
        {
            "msg": "swap_execution",
            "version": 1,
            "data": rlp([offer_id, timestamp])
        }
    """

    fields = [
        ('offer_id', hash32),
        ('timestamp', int256),
    ]

    def __init__(self, offer_id, timestamp):
        super(SwapExecution, self).__init__(offer_id, timestamp)


class SwapCompleted(SwapExecution):
    """`SwapCompleted` can be used by the commitment service after a successful swap,
    in order to build its reputation.

    Data:
        offer_id = offer.offer_id
        timestamp = int256 <unix timestamp (ms) of the last swap confirmation>

    Broadcast:
        {
            "msg": "swap_completed",
            "version": 1,
            "data": rlp([offer_id, timestamp])
        }
    """

    def __init__(self, offer_id, timestamp):
        super(SwapCompleted, self).__init__(offer_id, timestamp)

msg_types_map = dict(
        ping=Ping,
        offer=Offer,
        market_offer=ProvenOffer,
        commitment=Commitment,
        commitment_proof=CommitmentProof,
        commitment_service=CommitmentServiceAdvertisement,
        swap_executed=SwapExecution,
        swap_completed=SwapCompleted,
        )

types_msg_map = {value: key for key, value in msg_types_map.items()}


class Envelope(object):
    """Class to pack (`Envelope.envelop`) and unpack (`Envelope.open`) rlp messages
    in a broadcastable JSON-envelope. The rlp-data fields will be base64 encoded.
    """

    version = 1

    def __init__(self):
        pass

    @staticmethod
    def encode(data):
        return base64.encodestring(rlp.encode(data))

    @staticmethod
    def decode(data):
        return rlp.decode(base64.decodestring(data))

    @classmethod
    def open(cls, data):
        """Unpack the message data and return a message instance.
        """
        try:
            envelope = json.loads(data)
            assert isinstance(envelope, dict)
        except ValueError:
            raise ValueError("JSON-Envelope could not be decoded")

        if envelope['version'] != cls.version:
            raise ValueError("Message version mismatch! want:{} got:{}".format(
                Envelope.version, envelope['msg']))

        klass = msg_types_map[envelope['msg']]
        message = klass.deserialize(cls.decode(envelope['data']))

        return message

    @classmethod
    def envelop(cls, message):
        """Wrap the message in a json envelope.
        """
        assert isinstance(message, RLPHashable)
        envelope = dict(
                version=Envelope.version,
                msg=types_msg_map[message.__class__],
                data=cls.encode(message.serialize(message)),
                )
        return json.dumps(envelope)
