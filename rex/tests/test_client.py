from rex.client import OrderBook
from gen_orderbook_mock import gen_orderbook, gen_orderhistory
import gevent


def test_order_add():
    data = gen_orderbook(num_entries=5)

    book = OrderBook()
    assert len(book) == 0

    bids = data['bids']

    for bid in bids:
        print(bid)
        address = bid['address']
        price = bid['price']
        amount = bid['amount']
        book.add(address, price, amount)

    assert len(book) == 5


#def test_order_match():
#    book = OrderBook()
#
#    book.add(0, BTC(10), ETH(10))
#    book.add(1, ETH(10), BTC(10))
#
#    book.match()
#    gevent.sleep(1)
#
#    assert len(book.matched_orders) == 2
#    assert book.matched_orders[0][0] == 0
#    assert book.matched_orders[1][0] == 1
