import pytest
from raidex.raidex_node.order.offer import OfferType
from raidex.raidex_node.order.limit_order import LimitOrder


@pytest.fixture
def limit_order_as_dict(random_id):

    data = dict()
    data['order_id'] = random_id
    data['order_type'] = 'BUY'
    data['amount'] = 1
    data['price'] = 1
    data['lifetime'] = 60

    return data


@pytest.fixture
def limit_order_as_dict_without_order_id(limit_order_as_dict):
    del limit_order_as_dict['order_id']
    return limit_order_as_dict


@pytest.fixture
def limit_order_as_dict_sell(limit_order_as_dict):
    limit_order_as_dict['order_type'] = 'SELL'
    return limit_order_as_dict


@pytest.fixture
def limit_order(limit_order_as_dict):
    return LimitOrder.from_dict(limit_order_as_dict)


@pytest.mark.parametrize(argnames='limit_order_as_dict',
                         argvalues=[limit_order_as_dict,
                                    limit_order_as_dict_sell,
                                    limit_order_as_dict_without_order_id],
                         indirect=True)
def test_limit_order_from_dict_with_id(limit_order_as_dict):

    order = LimitOrder.from_dict(limit_order_as_dict)

    assert isinstance(order, LimitOrder)
    assert order.order_id == limit_order_as_dict['order_id']

    if limit_order_as_dict['order_type'] == 'BUY':
        assert order.order_type == OfferType.BUY
    elif limit_order_as_dict['order_type'] == 'SELL':
        assert order.order_type == OfferType.SELL

    assert order.amount == limit_order_as_dict['amount']
    assert order.price == limit_order_as_dict['price']
    assert order.lifetime == limit_order_as_dict['lifetime']


def test_add_offer(limit_order, internal_offer):

    limit_order.add_offer(internal_offer)
    assert internal_offer == limit_order.get_open_offers()[0]
    assert len(limit_order.get_open_offers()) == 1


# TODO needs better testing for multiple offers limit order state
def test_limit_order_states(limit_order, internal_offer):
    limit_order.add_offer(internal_offer)

    assert limit_order.open
    assert not limit_order.completed
    assert not limit_order.canceled
    assert limit_order.amount_traded == 0

    internal_offer.to_completed()

    assert not limit_order.open
    assert limit_order.completed
    assert not limit_order.canceled
    assert limit_order.amount_traded == 1

    internal_offer.to_canceled()

    assert not limit_order.open
    assert not limit_order.completed
    assert limit_order.canceled
    assert limit_order.amount_traded == 0
