from rex.client import LimitOrder, OfferView, OrderManager, OrderBook, Currency
from gen_orderbook_mock import gen_orderbook, gen_orderhistory
import gevent


def test_limitorder_comparison():
    order1 = LimitOrder(amount=50, price=5.)
    order2 = LimitOrder(amount=100, price=1.)
    order3 = LimitOrder(amount=100, price=2.)
    order4 = LimitOrder(amount=100, price=1.)

    assert order1 == order1
    assert order2 != order4
    assert order2 < order4 < order3 < order1
    assert order1 >= order3 >= order4 >= order2


class MockManager(object):
    id_ = 0

    def limit_order(self, pair, type_, amount, price, ttl=600):
        return LimitOrder(
            amount=amount, price=price, order_id=self.get_next_id(), ttl=ttl)

    def get_next_id(self):
        self.id_ = self.id_ + 1
        return self.id_


offerview_data = [
    { 'message_type': 'limit', 'type': 'sell', 'amount': 100, 'price': 15., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 120, 'price': 20., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 130, 'price': 18., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 90,  'price': 13., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 80,  'price': 18., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 80,  'price': 20., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 100, 'price': 16., 'ttl': 300 },
    { 'message_type': 'limit', 'type': 'sell', 'amount': 20,  'price': 14., 'ttl': 300 },
]


def test_offerview_ordering():
    manager = MockManager()
    offers = OfferView(manager, (Currency.ETH, Currency.BTC))
    offer_ids = [offers.add_offer(offer) for offer in offerview_data]

    assert len(offers) == len(offerview_data)
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

    # test removal
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)

    assert len(offers) == len(offerview_data) - 3
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))


def test_matching():
    manager = OrderManager()
    pair = (Currency.ETH, Currency.BTC)
    orderbook = OrderBook(manager, pair)
    offers = orderbook.bids
    offer_ids = [offers.add_offer(offer) for offer in offerview_data]
    gevent.sleep(20)
