import pytest
import gevent
from raidex.utils.greenlet_helper import TimeoutHandler
from raidex.utils.timestamp import seconds_to_timeout
from raidex.exceptions import AlreadyTimedOutException


@pytest.fixture
def timeout_handler():
    return TimeoutHandler()


def test_create_new_timeout(timeout_handler, basic_offer):

    success = timeout_handler.create_new_timeout(basic_offer)

    assert success
    assert timeout_handler._has_greenlet(basic_offer.offer_id)
    assert not timeout_handler.timeout_greenlets[basic_offer.offer_id].dead
    assert not timeout_handler.timeout_greenlets[basic_offer.offer_id].ready()


def test_create_new_timeout_of_existing(timeout_handler, basic_offer):

    success = timeout_handler.create_new_timeout(basic_offer, 10)
    assert success
    old_timeout_greenlet = timeout_handler.timeout_greenlets[basic_offer.offer_id]

    success = timeout_handler.create_new_timeout(basic_offer)
    assert success

    assert not timeout_handler.timeout_greenlets[basic_offer.offer_id].dead
    assert old_timeout_greenlet.dead


def test_create_new_timeout_of_timeouted_offer(timeout_handler, basic_offer):
    success = timeout_handler.create_new_timeout(basic_offer, seconds_to_timeout(basic_offer.timeout_date))
    assert success
    timeout_greenlet = timeout_handler.timeout_greenlets[basic_offer.offer_id]
    gevent.wait([timeout_greenlet])
    assert timeout_greenlet.dead

    with pytest.raises(AlreadyTimedOutException):
        timeout_handler.create_new_timeout(basic_offer)


def test_clean_up_timeout(timeout_handler, basic_offer):
    offer_id = basic_offer.offer_id

    timeout_handler.create_new_timeout(basic_offer)
    timeout_greenlet = timeout_handler.timeout_greenlets[offer_id]
    timeout_handler.clean_up_timeout(offer_id)

    assert not timeout_handler._has_greenlet(offer_id)
    assert timeout_greenlet.dead



