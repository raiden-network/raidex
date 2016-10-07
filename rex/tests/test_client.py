import gevent
import time

from rex.client import Order, OfferView, OrderManager, OrderBook, Currency, OrderType

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
                  for offer in offers if offer.bid_token==assets[0]]
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


def test_matching(offers, assets):
    manager = OrderManager()

    pair = (assets[0], assets[1])
    orderbook = OrderBook(asset_pair=pair)
    manager.add_orderbook(pair, orderbook)

    for offer in offers:
        if offer.ask_token == assets[0]:
            orderbook.insert_from_msg(offer)
    gevent.sleep(2)

    for offer in offers:
        if offer.bid_token == assets[0]:
            orderbook.insert_from_msg(offer)
            break

    gevent.sleep(1)
