import json
import time
import pytest

from ethereum.utils import sha3

from rex.messages import (Offer, Commitment, CommitmentProof, ProvenOffer,
        Envelope)
from rex.utils import milliseconds, ETHER_TOKEN_ADDRESS


def test_offer(assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    assert isinstance(o, Offer)
    serial = o.serialize(o)
    assert_serialization(o)
    assert_envelope_serialization(o)
    assert Offer.deserialize(serial) == o
    assert o.timed_out()


def test_hashable(assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    assert o.hash


def test_signed(accounts, assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    o.sign(accounts[0].privatekey)
    assert o.sender == accounts[0].address


def test_commitments(offers, accounts):
    offer = offers[0]
    commitment_service = accounts[2]
    maker = filter(lambda acc: acc.address == offer.sender, accounts)[0]

    commitment = Commitment(offer.offer_id, offer.hash, offer.timeout, 42)
    commitment.sign(maker.privatekey)
    assert_serialization(commitment)
    assert_envelope_serialization(commitment)

    commitment_proof = CommitmentProof(commitment.signature)
    commitment_proof.sign(commitment_service.privatekey)
    assert commitment_proof.sender == commitment_service.address
    assert_serialization(commitment_proof)
    assert_envelope_serialization(commitment_proof)

    proven_offer = ProvenOffer(offer, commitment, commitment_proof)
    proven_offer.sign(maker.privatekey)
    assert_serialization(proven_offer)
    assert_envelope_serialization(proven_offer)

    assert proven_offer.offer.sender == commitment.sender
    assert proven_offer.commitment_proof.commitment_sig == proven_offer.commitment.signature
    assert proven_offer.commitment.timeout == proven_offer.offer.timeout


def assert_serialization(serializable):
    serialized = serializable.serialize(serializable)
    assert serializable.__class__.deserialize(serialized) == serializable


def test_offers(offers, accounts):
    senders = [acc.address for acc in accounts]
    for offer in offers:
        assert offer.sender in senders
        assert not offer.timed_out(at=milliseconds.time_int() - 3600 * 1000)  # pretend we come from the past


def test_cs_advertisements(commitment_service_advertisements, commitment_services):
    cservices = [cs.address for cs in commitment_service_advertisements]
    for advertisement in commitment_service_advertisements:
        # the only sender of a CS-Ad can be the CS itself:
        assert advertisement.address == advertisement.sender
        assert advertisement.address in cservices
        assert advertisement.commitment_asset == ETHER_TOKEN_ADDRESS
        # fee_rate represented as int(float_rate/uint32.max_int)
        assert isinstance(advertisement.fee_rate, int)
        assert 0 <= advertisement.fee_rate <= 2 ** 32


def test_swap_execution(offers, accounts, maker_swap_executions, taker_swap_executions):
    time_ = milliseconds.time_int()
    senders = [acc.address for acc in accounts]

    # there need to exist two swap executions, one from the offer.sender and one from the taker
    # dont include this logic in the unit test!
    for sw_execution in taker_swap_executions + maker_swap_executions:
        assert sw_execution.sender in senders
        assert time_ > sw_execution.timestamp  # should be in the past


def test_swap_completeds(offers, commitment_services, swap_completeds):
    time_ = milliseconds.time_int()
    senders = [cs.address for cs in commitment_services]

    # there need to exist two swap executions, one from the offer.sender and one from the taker
    # dont include this logic in the unit test!
    for sw_completed in swap_completeds:
        assert sw_completed.sender in senders
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
