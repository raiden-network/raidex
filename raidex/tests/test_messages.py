import json
import random
from operator import attrgetter

import pytest
from ethereum.utils import sha3, big_endian_to_int
from raidex.messages import (
    SignatureMissingError,
    Signed,
    SwapOffer,
    Commitment,
    CommitmentProof,
    ProvenOffer,
    Envelope,
    SwapCompleted,
    SwapExecution,
    CommitmentServiceAdvertisement
)
from raidex.utils import timestamp, ETHER_TOKEN_ADDRESS, make_privkey_address
from raidex.commitment_service.mock import CommitmentServiceMock
from raidex.signing import Signer

# TODO refactor this tests, especially the fixtures

UINT32_MAX_INT = 2 ** 32


@pytest.fixture()
def commitment_service():
    return CommitmentServiceMock(Signer.random(), None, None, fee_rate=0.1)


def test_offer(assets):
    o = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), timestamp.time() - 10)
    assert isinstance(o, SwapOffer)
    serial = o.serialize(o)
    assert_serialization(o)
    assert_envelope_serialization(o)
    assert SwapOffer.deserialize(serial) == o
    assert o.timed_out()
    assert not o.timed_out(at=timestamp.time() - 3600 * 1000)  # pretend we come from the past


def test_hashable(assets):
    o = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    assert o.hash


def test_signing(accounts):
    c = Commitment(offer_id=10, offer_hash=sha3('offer id'), timeout=timestamp.time_plus(milliseconds=100),
                            amount=10)
    c_unsigned = Commitment(offer_id=10, offer_hash=sha3('offer id'), timeout=timestamp.time_plus(milliseconds=100),
                            amount=10)
    assert c == c_unsigned
    c.sign(accounts[0].privatekey)
    assert c.sender == accounts[0].address
    assert_serialization(c)
    assert_serialization(c_unsigned)

    #check hashes:
    assert c._hash_without_signature == c_unsigned._hash_without_signature
    assert c.hash != c_unsigned.hash
    assert c_unsigned.signature == ''

    # check that getting the sender of unsigned 'Signed'-message raises an error
    c_unsigned_deserialized = Commitment.deserialize(c_unsigned.serialize(c_unsigned))

    raised = False
    try:
        c_unsigned_deserialized.sender
    except SignatureMissingError:
        raised = True
    assert raised


def test_commitments(assets, commitment_service, accounts):
    offer = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    maker = accounts[0]

    commitment = Commitment(offer.offer_id, offer.hash, offer.timeout, 42)
    commitment.sign(maker.privatekey)
    assert_serialization(commitment)
    assert_envelope_serialization(commitment)

    commitment_proof = CommitmentProof(commitment.signature)
    commitment_service._cs_sign(commitment_proof)
    assert commitment_proof.sender == commitment_service.commitment_service_address
    assert_serialization(commitment_proof)
    assert_envelope_serialization(commitment_proof)

    proven_offer = ProvenOffer(offer, commitment, commitment_proof)
    proven_offer.sign(maker.privatekey)
    assert_serialization(proven_offer)
    assert_envelope_serialization(proven_offer)

    assert proven_offer.sender == commitment.sender
    assert proven_offer.commitment_proof.commitment_sig == proven_offer.commitment.signature
    assert proven_offer.commitment.timeout == proven_offer.offer.timeout


def assert_serialization(serializable):
    serialized = serializable.serialize(serializable)
    deserialized = serializable.__class__.deserialize(serialized)
    assert deserialized == serializable
    for field in serializable.__class__.fields:
        getter = attrgetter(field[0])
        assert getter(deserialized) == getter(serializable)
    if isinstance(serializable, Signed):
        assert deserialized.signature == serializable.signature


def test_cs_advertisements(commitment_service):
    csa = CommitmentServiceAdvertisement(
        commitment_service.commitment_service_address,
        ETHER_TOKEN_ADDRESS,
        int(commitment_service.fee_rate / UINT32_MAX_INT)
    )
    commitment_service._cs_sign(csa)
    assert_serialization(csa)
    assert_envelope_serialization(csa)
    assert csa.sender == commitment_service.commitment_service_address


def test_swap_execution(accounts):
    maker = accounts[0]
    sw_execution = SwapExecution(big_endian_to_int(sha3('offer id')), timestamp.time())
    sw_execution.sign(maker.privatekey)
    assert_serialization(sw_execution)
    assert_envelope_serialization(sw_execution)
    time_ = timestamp.time_plus(1)
    assert sw_execution.sender == maker.address
    assert time_ > sw_execution.timestamp  # should be in the past


def test_swap_completed(commitment_service):
    sw_completed = SwapCompleted(big_endian_to_int(sha3('offer id')), timestamp.time())
    commitment_service._cs_sign(sw_completed)
    time_ = timestamp.time_plus(1)
    assert_serialization(sw_completed)
    assert_envelope_serialization(sw_completed)
    assert sw_completed.sender == commitment_service.commitment_service_address
    assert time_ > sw_completed.timestamp  # should be in the past


def assert_envelope_serialization(message):
    b64 = Envelope.encode(message.serialize(message))
    assert message.serialize(message) == Envelope.decode(b64)
    envelope = Envelope.envelop(message)
    assert Envelope.open(envelope) == message, envelope

    with pytest.raises(ValueError):
        envelope_dict = json.loads(envelope)
        envelope_dict['version'] = 2
        Envelope.open(json.dumps(envelope_dict))
