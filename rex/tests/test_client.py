import gevent
import time

from ethereum.utils import sha3

from rex.client import Order, OfferView, OrderManager, OrderBook, OrderType
from rex.messages import Offer


def test_order_comparison(assets):
    pair = (assets[0], assets[1])
    timeouts = [time.time() + i for i in range(0, 4)]
    order1 = Order(pair=pair, type_=OrderType.BID, amount=50, price=5., timeout=timeouts[0])
    order2 = Order(pair=pair, type_=OrderType.BID, amount=100, price=1., timeout=timeouts[1])
    order3 = Order(pair=pair, type_=OrderType.BID, amount=100, price=2., timeout=timeouts[2])
    order4 = Order(pair=pair, type_=OrderType.BID, amount=100, price=1., timeout=timeouts[3])

    assert order1 == order1
    assert order2 != order4
    assert order2 < order4 < order3 < order1
    assert order1 >= order3 >= order4 >= order2


def test_offerview_ordering(offers, assets):
    # filter correct asset_pair and add type_ manually
    compare_pair = (assets[0], assets[1])
    bid_orders = [Order.from_offer_message(offer, compare_pair)
                  for offer in offers if offer.bid_token == assets[0]]
    offers = OfferView(pair=compare_pair, type_=OrderType.BID)
    offer_ids = [offers.add_offer(order) for order in bid_orders]

    assert len(offers) == len(bid_orders)
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

    # test removal
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)
    offers.remove_offer(offers.orders.min_item()[0].order_id)

    assert len(offers) == len(bid_orders) - 3
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))


def test_simple_matching(assets):
    manager = OrderManager()

    pair = (assets[0], assets[1])
    orderbook = OrderBook(asset_pair=pair)
    manager.add_orderbook(pair, orderbook)

    # ask orders
    order_ids = []
    for i in range(8):
        order_ids.append(orderbook.insert_from_msg(
            Offer(
                assets[0], 10, assets[1], 10,
                sha3('offer {}'.format(i)),
                int(time.time()) * 1000 + 60000
            )
        ))
    gevent.sleep(.1)

    # bid order
    offer = Offer(
        assets[1], 10, assets[0], 10,
        sha3('offer {}'.format(i)),
        int(time.time()) * 1000 + 60000,
    )
    order_id = orderbook.insert_from_msg(offer)

    event = gevent.event.AsyncResult()

    def check_match(offers):
        assert len(offers) == 1
        order = offers[0][0]
        assert order.order_id in order_ids
        event.set(True)

    order = orderbook.bids.get_offer_by_id(order_id)
    orderbook.run_task_for_order(order, callback=check_match)
    event.wait(1.)
