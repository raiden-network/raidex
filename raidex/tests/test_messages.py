import json
import random
from operator import attrgetter

import pytest
from ethereum.utils import sha3, big_endian_to_int

from raidex.messages import (
    SignatureMissingError,
    Signed,
    Offer,
    Commitment,
    CommitmentProof,
    ProvenOffer,
    Envelope,
    SwapCompleted,
    SwapExecution,
    CommitmentServiceAdvertisement
)

from raidex.utils import milliseconds, ETHER_TOKEN_ADDRESS


@pytest.fixture()
def taker_swap_executions(accounts, offer_msgs):
    taker_swap_executions = []
    for offer in offer_msgs:
        taker = None
        while taker is None or taker.address == offer.sender:
            taker = random.choice(accounts)
        sw_execution = SwapExecution(offer.offer_id, milliseconds.time_int())
        sw_execution.sign(taker.privatekey)
        taker_swap_executions.append(sw_execution)
    return taker_swap_executions


@pytest.fixture()
def maker_swap_executions(accounts, offer_msgs):
    maker_swap_executions_ = []
    for offer in offer_msgs:
        maker = None
        for acc in accounts:
            if offer.sender == acc.address:
                maker = acc
                break
        if maker is None:
            continue
        sw_execution = SwapExecution(offer.offer_id, milliseconds.time_int())
        sw_execution.sign(maker.privatekey)
        maker_swap_executions_.append(sw_execution)
    return maker_swap_executions_


@pytest.fixture()
def swap_completeds(commitment_services, offer_msgs):
    swap_completeds_ = []
    for offer in offer_msgs:
        cs = random.choice(commitment_services)
        # TODO eventually construct them in a way, that swap executions have an earlier time
        sw_completed = SwapCompleted(offer.offer_id, milliseconds.time_int())
        sw_completed.sign(cs.private_key)
        swap_completeds_.append(sw_completed)
    return swap_completeds_


@pytest.fixture()
def commitment_service_advertisements(commitment_services):
    commitment_service_advertisements_ = []
    for cs in commitment_services:
        csa = CommitmentServiceAdvertisement(
            cs.address,
            cs.commitment_asset,
            cs.fee_rate
        )
        csa.sign(cs.private_key)
        commitment_service_advertisements_.append(csa)
    return commitment_service_advertisements_


def test_offer(assets, accounts):
    o = Offer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    acc = accounts[0]
    assert isinstance(o, Offer)
    serial = o.serialize(o)
    assert_serialization(o)
    assert_envelope_serialization(o)
    assert Offer.deserialize(serial) == o
    assert o.timed_out()


def test_hashable(assets):
    o = Offer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    assert o.hash


def test_signing(accounts, assets):
    o = Offer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    o_unsigned = Offer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    # not signed yet, so must be equal
    assert o == o_unsigned
    o.sign(accounts[0].privatekey)
    assert o.sender == accounts[0].address
    assert_serialization(o)
    assert_serialization(o_unsigned)

    #check hashes:
    assert o._hash_without_signature == o_unsigned._hash_without_signature
    assert o.hash != o_unsigned.hash
    assert o_unsigned.signature == ''

    # check that getting the sender of unsigned 'Signed'-message raises an error
    o_unsigned_deserialized = Offer.deserialize(o_unsigned.serialize(o_unsigned))
    raised = False
    try:
        o_unsigned_deserialized.sender
    except SignatureMissingError:
        raised = True
    assert raised


def test_commitments(offer_msgs, accounts):
    offer = offer_msgs[0]
    commitment_service = accounts[2]
    maker = filter(lambda acc: acc.address == offer.sender, accounts)[0]

    commitment = Commitment(offer.offer_id, offer.timeout, 42)
    commitment.sign(maker.privatekey)
    assert_serialization(commitment)
    assert_envelope_serialization(commitment)

    proof = commitment.compute_signed_signature(commitment_service.privatekey)
    commitment_proof = CommitmentProof(commitment.signature, proof)
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
    deserialized = serializable.__class__.deserialize(serialized)
    assert deserialized == serializable
    for field in serializable.__class__.fields:
        getter = attrgetter(field[0])
        assert getter(deserialized) == getter(serializable)
    if isinstance(serializable, Signed):
        assert deserialized.signature == serializable.signature


def test_offers(offer_msgs, accounts):
    senders = [acc.address for acc in accounts]
    for offer in offer_msgs:
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


def test_swap_execution(offer_msgs, accounts, maker_swap_executions, taker_swap_executions):
    time_ = milliseconds.time_int()
    senders = [acc.address for acc in accounts]

    # there need to exist two swap executions, one from the offer.sender and one from the taker
    # dont include this logic in the unit test!
    for sw_execution in taker_swap_executions + maker_swap_executions:
        assert sw_execution.sender in senders
        assert time_ > sw_execution.timestamp  # should be in the past


def test_swap_completeds(offer_msgs, commitment_services, swap_completeds):
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

