from rex.client import Order, OfferView, OrderManager, OrderBook, Currency
from gen_orderbook_mock import gen_orderbook, gen_orderhistory
import gevent


def test_order_comparison():
    pair = (Currency.ETH, Currency.BTC)
    order1 = Order(pair=pair, amount=50, price=5.)
    order2 = Order(pair=pair, amount=100, price=1.)
    order3 = Order(pair=pair, amount=100, price=2.)
    order4 = Order(pair=pair, amount=100, price=1.)

    assert order1 == order1
    assert order2 != order4
    assert order2 < order4 < order3 < order1
    assert order1 >= order3 >= order4 >= order2


class MockManager(object):
    id_ = 0

    def limit_order(self, pair, type_, amount, price, ttl=600):
        return Order(
            amount=amount, price=price, order_id=self.get_next_id(), ttl=ttl, type_=type_)

    def get_next_id(self):
        self.id_ = self.id_ + 1
        return self.id_


offer_messages = [
    { 'bid_token': 'ETH', 'bid_amount': 10, 'ask_token': 'BTC', 'ask_amount': 100, 'offer_id': 0, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 12, 'ask_token': 'BTC', 'ask_amount': 120, 'offer_id': 1, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 13, 'ask_token': 'BTC', 'ask_amount': 130, 'offer_id': 2, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 9,  'ask_token': 'BTC', 'ask_amount': 90,  'offer_id': 3, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 8,  'ask_token': 'BTC', 'ask_amount': 80,  'offer_id': 4, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 8,  'ask_token': 'BTC', 'ask_amount': 80,  'offer_id': 5, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 10, 'ask_token': 'BTC', 'ask_amount': 100, 'offer_id': 6, 'timeout': 300 },
    { 'bid_token': 'ETH', 'bid_amount': 2,  'ask_token': 'BTC', 'ask_amount': 20,  'offer_id': 7, 'timeout': 300 },
]


def test_offerview_ordering():
    manager = MockManager()
    offers = OfferView(manager, (Currency.ETH, Currency.BTC))
    offer_ids = [offers.add_offer(offer) for offer in offer_messages]

    assert len(offers) == len(offer_messages)
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

    # test removal
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)

    assert len(offers) == len(offer_messages) - 3
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))


def test_matching():
    manager = OrderManager()
    pair = (Currency.ETH, Currency.BTC)
    orderbook = OrderBook(manager, pair)
    offer_ids = [orderbook.asks.add_offer(offer) for offer in offer_messages]
    gevent.sleep(2)

    # try to buy from the previous sell data
    buy_data = {
        'bid_token': 'BTC', 'bid_amount': 20,  'ask_token': 'ETH', 'ask_amount': 2,  'offer_id': 7, 'timeout': 300,
    }
    offer_id = orderbook.bids.add_offer(buy_data)
    gevent.sleep(3)
