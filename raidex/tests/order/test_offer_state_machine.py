import pytest

from raidex.messages import CommitmentProof
from raidex.utils import random_secret, keccak


@pytest.fixture
def commitment_proof(internal_offer):

    secret = random_secret()

    return CommitmentProof(None, secret, keccak(secret), internal_offer.offer_id)


def test_timeout_offer(internal_offer):

    assert internal_offer.state == 'created'
    assert internal_offer.status == 'open'

    internal_offer.timeout()

    assert internal_offer.state == 'cancellation_requested'
    assert internal_offer.status == 'open'


def test_receive_commitment_prove(internal_offer):
    internal_offer.initiating()

    internal_offer.receive_commitment_proof(commitment_proof)
    assert internal_offer.state == 'proved'
    assert internal_offer.status == 'open'

    internal_offer.timeout()
    assert internal_offer.state == 'cancellation_requested'
    assert internal_offer.status == 'open'


def test_receive_published_offer(internal_offer):
    internal_offer.initiating()

    internal_offer.receive_commitment_proof(commitment_proof)
    assert internal_offer.state == 'proved'
    assert internal_offer.status == 'open'

    internal_offer.received_offer()
    assert internal_offer.state == 'published'
    assert internal_offer.status == 'open'
