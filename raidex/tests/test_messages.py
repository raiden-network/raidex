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
from raidex.utils import milliseconds, ETHER_TOKEN_ADDRESS, make_privkey_address
from raidex.commitment_service.server import CommitmentService

# TODO refactor this tests, especially the fixtures

UINT32_MAX_INT = 2 ** 32


@pytest.fixture()
def commitment_service():
    privkey, _ = make_privkey_address()
    # is None here, since the broker functionality won't be used
    message_broker = None
    return CommitmentService(message_broker, privkey, 0.01)


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
def swap_completeds(commitment_service, offer_msgs):
    swap_completeds_ = []
    for offer in offer_msgs:
        sw_completed = SwapCompleted(offer.offer_id, milliseconds.time_int())
        commitment_service._sign(sw_completed)
        swap_completeds_.append(sw_completed)
    return swap_completeds_


def test_offer(assets, accounts):
    o = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    acc = accounts[0]
    assert isinstance(o, SwapOffer)
    serial = o.serialize(o)
    assert_serialization(o)
    assert_envelope_serialization(o)
    assert SwapOffer.deserialize(serial) == o
    assert o.timed_out()


def test_hashable(assets):
    o = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    assert o.hash


def test_signing(accounts, assets):
    o = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
    o_unsigned = SwapOffer(assets[0], 100, assets[1], 110, big_endian_to_int(sha3('offer id')), 10)
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
    o_unsigned_deserialized = SwapOffer.deserialize(o_unsigned.serialize(o_unsigned))

    raised = False
    try:
        o_unsigned_deserialized.sender
    except SignatureMissingError:
        raised = True
    assert raised


def test_commitments(offer_msgs, commitment_service, accounts):
    offer = offer_msgs[0]
    maker = filter(lambda acc: acc.address == offer.sender, accounts)[0]

    commitment = Commitment(offer.offer_id, offer.hash, offer.timeout, 42)
    commitment.sign(maker.privatekey)
    assert_serialization(commitment)
    assert_envelope_serialization(commitment)

    commitment_proof = CommitmentProof(commitment.signature)
    commitment_service._sign(commitment_proof)
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


def test_cs_advertisements(commitment_service):
    csa = CommitmentServiceAdvertisement(
        commitment_service.address,
        ETHER_TOKEN_ADDRESS,
        int(commitment_service.fee_rate / UINT32_MAX_INT)
    )
    commitment_service._sign(csa)
    assert commitment_service.address == csa.sender
    assert csa.address == commitment_service.address
    assert csa.commitment_asset == ETHER_TOKEN_ADDRESS
    # fee_rate represented as int(float_rate/uint32.max_int)
    assert isinstance(csa.fee_rate, int)
    assert 0 <= csa.fee_rate <= 2 ** 32
    assert csa.fee_rate == int(commitment_service.fee_rate / UINT32_MAX_INT)


def test_swap_execution(offer_msgs, accounts, maker_swap_executions, taker_swap_executions):
    time_ = milliseconds.time_plus(1)
    senders = [acc.address for acc in accounts]

    for sw_execution in taker_swap_executions + maker_swap_executions:
        assert sw_execution.sender in senders
        assert time_ > sw_execution.timestamp  # should be in the past


def test_swap_completeds(offer_msgs, commitment_service, swap_completeds):
    time_ = milliseconds.time_plus(1)

    for sw_completed in swap_completeds:
        assert sw_completed.sender == commitment_service.address
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
