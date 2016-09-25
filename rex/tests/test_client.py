from rex.client import OrderBook, BTC, ETH


def test_order_add():
    book = OrderBook()
    assert len(book) == 0

    book.exchange(BTC(10), ETH(20))

    assert len(book) == 1
