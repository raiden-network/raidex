import gevent
from bintrees import FastRBTree
from bottle import request, Bottle, abort
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from rex.gen_orderbook_mock import gen_orderbook


app = Bottle()

@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        try:
            message = wsock.receive()
            wsock.send("Your message was: %r" % message)
        except WebSocketError:
            break


class ClientService(object):

    def __init__(self):
        self.orderbooks = dict() # key: asset_pair, value: OrderBook instance

    def get_orderbook_by_asset_pair(self, asset_pair):
        if asset_pair not in self.orderbooks.keys():
            # instantiate empty orderbook
            mocked_orderbook = OrderBook()
            # fill with mock data
            mocked_orderbook.orders = gen_orderbook()
            self.orderbooks[asset_pair] = mocked_orderbook
            return mocked_orderbook
        else:
            return self.orderbooks[asset_pair]


class OfferView(object):

    def __init__(self):
        self.offer_id = 0

    def add_offer(offer_message):
        return self.offer_id

    def remove_offer(offer_id):
        pass


class OrderBook(object):

    def __init__(self):
        self.ordersindex = FastRBTree()
        self.orders = dict()

    def add(self, address, price, amount, timeout):
        id_ = sha3(address + str(price * amount))
        self.ordersindex.insert(price)
        assert id_ not in self.orders
        self.orders[id_] = (address, price, amount, timeout)

    @property
    def bids(self): # TODO: implement __iter__() and next() for the data structure chosen for list() representation
        assert len(self.orders) % 2 == 0
        half_list = int(len(self.orders) / 2)
        return reversed(self.orders[:half_list])

    @property
    def asks(self):
        assert len(self.orders) % 2 == 0
        half_list = int(len(self.orders) / 2)
        return self.orders[half_list:]

    def __iter__(self):
        return iter(self.ordersindex)

    def __len__(self):
        return len(self.ordersindex)

    def insert(self, elem):
        pass

    def remove(self, elem):
        pass

    def find_best(self):
        pass


class OrderTask(gevent.Greenlet):

    def __init__(self, offerviews, order_id):
        super(OrderTask, self).__init__()
        self.offerviews = offerviews
        self.order_id = order_id
        self.stop_event = AsyncResult()

    def _run(self):  # pylint: disable=method-hidden
        stop = None

        while stop is None:
            # TODO
            # tries to match 
            for _address, price, amount in self.book.orders:
                # look for amount asked with a maximum of price
                if 
                pass

            stop = self.stop_event.wait(0)

    def stop(self):
        self.stop_event.set(True)


class OrderManager(object):

    def __init__(self):
        self.orderbooks = dict()
        self.trades = dict()
        self.order_id = 0  # increment per new order

    def add_orderbook(self, pair, orderbook):
        self.orderbooks[pair] = orderbook

    def get_order_book(self, pair):
        assert pair in self.orderbooks
        return self.orderbooks[pair]

    def get_trade_history(self, pair, num_trades):
        assert pair in self.trades
        return self.trades[pair]

    def limit_order(pair, type_, num_tokens, price) # returns internal order_id
        return order_id

    def market_order(pair, type_, num_tokens) # returns internal order_id
        return order_id

    def get_order_status(pair, order_id)
        pass

    def cancel_order(self, order_id):
        pass


if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 8080), app,
                        handler_class=WebSocketHandler)
    server.serve_forever()
