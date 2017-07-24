import json
from operator import attrgetter

import pytest
from ethereum.utils import sha3, big_endian_to_int
from raidex.messages import (
    SignatureMissingError,
    Signed,
    SwapOffer,
    MakerCommitment,
    TakerCommitment,
    CommitmentProof,
    ProvenCommitment,
    ProvenOffer,
    Envelope,
    SwapCompleted,
    SwapExecution,
    CommitmentServiceAdvertisement
)
from raidex.utils import timestamp, ETHER_TOKEN_ADDRESS


UINT32_MAX_INT = 2 ** 32


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
    timeout = timestamp.time_plus(milliseconds=100)
    c = MakerCommitment(offer_id=10, offer_hash=sha3('offer id'), timeout=timeout,
                            amount=10)
    c_unsigned = MakerCommitment(offer_id=10, offer_hash=sha3('offer id'), timeout=timeout,
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
    c_unsigned_deserialized = MakerCommitment.deserialize(c_unsigned.serialize(c_unsigned))

    raised = False
    try:
        c_unsigned_deserialized.sender
    except SignatureMissingError:
        raised = True
    assert raised


def test_maker_commitments(assets, accounts):
    offer = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    maker = accounts[0]
    commitment_service = accounts[1]

    commitment_msg = MakerCommitment(offer.offer_id, offer.hash, offer.timeout, 42)
    commitment_msg.sign(maker.privatekey)
    assert_serialization(commitment_msg)
    assert_envelope_serialization(commitment_msg)

    commitment_proof_msg = CommitmentProof(commitment_msg.signature)
    commitment_proof_msg.sign(commitment_service.privatekey)
    assert commitment_proof_msg.sender == commitment_service.address
    assert_serialization(commitment_proof_msg)
    assert_envelope_serialization(commitment_proof_msg)

    proven_offer_msg = ProvenOffer(offer, commitment_msg, commitment_proof_msg)
    proven_offer_msg.sign(maker.privatekey)
    assert_serialization(proven_offer_msg)
    assert_envelope_serialization(proven_offer_msg)

    # FIXME check if those are neccessary tests
    assert proven_offer_msg.sender == commitment_msg.sender
    assert proven_offer_msg.commitment_proof.commitment_sig == proven_offer_msg.commitment.signature
    assert proven_offer_msg.commitment.timeout == proven_offer_msg.offer.timeout


def test_taker_commitments(assets, accounts):
    offer = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    maker = accounts[0]
    commitment_service = accounts[1]

    commitment_msg = TakerCommitment(offer.offer_id, offer.hash, offer.timeout, 42)
    commitment_msg.sign(maker.privatekey)
    assert_serialization(commitment_msg)
    assert_envelope_serialization(commitment_msg)

    commitment_proof_msg = CommitmentProof(commitment_msg.signature)
    commitment_proof_msg.sign(commitment_service.privatekey)
    assert commitment_proof_msg.sender == commitment_service.address
    assert_serialization(commitment_proof_msg)
    assert_envelope_serialization(commitment_proof_msg)

    proven_commitment_msg = ProvenCommitment(commitment_msg, commitment_proof_msg)
    proven_commitment_msg.sign(maker.privatekey)
    assert_serialization(proven_commitment_msg)
    assert_envelope_serialization(proven_commitment_msg)

    # FIXME check if those are neccessary tests
    assert proven_commitment_msg.sender == commitment_msg.sender
    assert proven_commitment_msg.commitment_proof.commitment_sig == commitment_msg.signature
    assert proven_commitment_msg.commitment == commitment_msg


def assert_serialization(serializable):
    serialized = serializable.serialize(serializable)
    deserialized = serializable.__class__.deserialize(serialized)
    assert deserialized == serializable
    for field in serializable.__class__.fields:
        getter = attrgetter(field[0])
        assert getter(deserialized) == getter(serializable)
    if isinstance(serializable, Signed):
        assert deserialized.signature == serializable.signature


def test_commitment_service_advertisements(accounts):
    commitment_service = accounts[0]
    fee_rate = 0.1
    commitment_service_advertisement_msg = CommitmentServiceAdvertisement(
        commitment_service.address,
        ETHER_TOKEN_ADDRESS,
        int(fee_rate / UINT32_MAX_INT)
    )
    commitment_service_advertisement_msg.sign(commitment_service.privatekey)
    assert_serialization(commitment_service_advertisement_msg)
    assert_envelope_serialization(commitment_service_advertisement_msg)
    assert commitment_service_advertisement_msg.sender == commitment_service.address


def test_swap_execution(accounts):
    maker = accounts[0]
    swap_execution_msg = SwapExecution(big_endian_to_int(sha3('offer id')), timestamp.time())
    swap_execution_msg.sign(maker.privatekey)
    assert_serialization(swap_execution_msg)
    assert_envelope_serialization(swap_execution_msg)
    time_ = timestamp.time_plus(1)
    assert swap_execution_msg.sender == maker.address
    assert time_ > swap_execution_msg.timestamp  # should be in the past


def test_swap_completed(accounts):
    commitment_service = accounts[0]
    swap_completed_msg = SwapCompleted(big_endian_to_int(sha3('offer id')), timestamp.time())
    swap_completed_msg.sign(commitment_service.privatekey)
    time_ = timestamp.time_plus(1)
    assert_serialization(swap_completed_msg)
    assert_envelope_serialization(swap_completed_msg)
    assert swap_completed_msg.sender == commitment_service.address
    assert time_ > swap_completed_msg.timestamp  # should be in the past


def assert_envelope_serialization(message):
    b64 = Envelope.encode(message.serialize(message))
    assert message.serialize(message) == Envelope.decode(b64)
    envelope = Envelope.envelop(message)
    assert Envelope.open(envelope) == message, envelope

    with pytest.raises(ValueError):
        envelope_dict = json.loads(envelope)
        envelope_dict['version'] = 2
        Envelope.open(json.dumps(envelope_dict))
