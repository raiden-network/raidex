import gevent
import time
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

    def __init__(self, raiden, order_manager, commitment_manager, api):
        self.raiden = raiden
        self.commitment_manager = commitment_manager
        self.order_manager = order_manager
        self.api = api

    @property
    def assets(self):
        return NotImplementedError
        # returns assets and balances tradeable from raiden
        # requirement: have an open channel + deposit for that asset
        #TODO: get from the raiden instance
        pass

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

class CommitmentManager(object):

    def __init__(self, raiden):
        self.raiden = raiden
        self.commitment_services = dict()


    def commit(self, commitment_service_address, offer_id, commitment_deposit, timeout):
        # the client needs to have a channel with both assets with a CS to trade on that asset pair,
        # although it is not required for doing a commitment, which is only done in ether
        raise NotImplementedError
        if successful:
            notify_success(commitment_service_address, offer_id)
            signed_commitment = True
            return signed_commitment
        else:
            return False

    def notify_success(self, commitment_service_address, offer_id):
        raise NotImplementedError

    def make_commitment_deposit(self, commitment_service_address, deposit_amount):
        if commitment_service_address not in self.commitment_services:
            # TODO: initiate first commit
            successful = True  # XXX mock success return value, always successful
            if successful is True:
                self.commitment_services[commitment_service_address] = dict(balance=deposit_amount)
            else:
                return False
        else:
            # TODO: extend commitment_deposit
            successful = True  # XXX mock success return value, always successful
            if successful is True:
                self.commitment_services[commitment_service_address][balance] += deposit_amount
            else:
                return False
            # returns raiden receipt


class Order(object):

    def __init__(self, amount, order_id=None, ttl=600):
        self.order_id = order_id
        self.amount = amount
        # TODO: add removal of expired orders
        self.timeout = time.time() + ttl


class LimitOrder(Order):

    def __init__(self, amount, price, order_id=None, ttl=600):
        super(LimitOrder, self).__init__(amount=amount, order_id=order_id, ttl=ttl)
        self.price = price

    def __cmp__(self, other):
        if self.price == other.price and self.timeout == other.timeout and \
                self.order_id == other.order_id:
            return 0
        elif self.price < other.price or (
            self.price == other.price and self.timeout < other.timeout) or (
                self.price == other.price and self.timeout == other.timeout and \
                        self.order_id < other.order_id):
            return -1
        else:
            return 1

    def __repr__(self):
        return "LimitOrder<order_id={} amount={} price={} timeout={}>".format(
                self.order_id, self.amount, self.price, self.timeout)


class MarketOrder(Order):

    def __init__(self, amount, order_id=None, ttl=600):
        super(MarketOrder, self).__init__(amount=amount, order_id=order_id, ttl=ttl)

    def __cmp__(self, other):
        if self.timeout == other.timeout and self.order_id == other.order_id:
            return 0
        elif self.timeout < other.timeout or (
                self.timeout == other.timeout and self.order_id < other.order_id):
            return -1
        else:
            return 1


class OfferView(object):

    def __init__(self, manager):
        self.orders = FastRBTree()
        self.offer_by_id = dict()
        self.manager = manager

    def add_offer(self, offer_message):
        # TODO: using mock format, must define offer_message
        message_type = offer_message['message_type']
        type_ = offer_message['type']
        amount = offer_message['amount']
        price = offer_message.get('price')
        ttl = offer_message.get('ttl')

        if message_type == 'limit':
            order = self.manager.limit_order(pair=None, type_=type_, amount=amount, price=price, ttl=ttl)
        else:
            order = self.manager.market_order(pair=None, type_=type_, amount=amount, ttl=ttl)

        order.order_id = self.manager.get_next_id()
        self.orders.insert(order, order)
        self.offer_by_id[order.order_id] = order

        return order.order_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_by_id:
            order = self.offer_by_id[offer_id]
            self.orders.remove(order)
            del self.offer_by_id[offer_id]
            # TODO: publish removal?

    def __len__(self):
        return len(self.orders)

    def __iter__(self):
        return iter(self.orders)


class OrderBook(object):

    def __init__(self, manager, asset_pair):
        # FIXME: just for silver bullet
        ask_currency, bid_currency = asset_pair
        self.asks = get_orderbook_by_asset_pair(ask_currency, bid_currency)
        assert isinstance(self.asks, OfferView)
        assert self.asks.currencypair == (ask_currency, bid_currency)
        self.bids = get_orderbook_by_asset_pair(bid_currency, ask_currency)# cpair = (BTC/ETH)
        assert isinstance(self.bids, OfferView)
        assert self.bids.currencypair == (bid_currency, ask_currency)

        self.manager = manager
        self.bids = OfferView(self.manager)
        self.asks = OfferView(self.manager)
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

    def set_manager(self, manager):
        self.manager = manager

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

    def __init__(self, orderbook, order_id):
        super(OrderTask, self).__init__()
        self.orderbook = orderbook
        self.order_id = order_id
        self.stop_event = AsyncResult()

    def _run(self):  # pylint: disable=method-hidden
        stop = None

        while stop is None:
            order = self.orderbook[order_id]
            bids = self.orderbook.bids
            asks = self.orderbook.asks
            for _address, price, amount in bids:
                pass

            stop = self.stop_event.wait(0)

    def stop(self):
        self.stop_event.set(True)


class OrderManager(object):

    def __init__(self):
        self.orderbooks = dict()
        self.trades = dict()
        self.order_id = 0  # increment per new order

    def get_next_id(self):
        self.order_id = self.order_id + 1
        return self.order_id

    def add_orderbook(self, pair, orderbook):
        self.orderbooks[pair] = orderbook
        orderbook.set_manager(self)

    def get_order_book(self, pair):
        assert pair in self.orderbooks
        return self.orderbooks[pair]

    def get_trade_history(self, pair, num_trades):
        assert pair in self.trades
        return self.trades[pair]

    def _spawn_order(self, order):
        order_id = order.order_id = self.get_next_id()
        gevent.spawn(OrderTask, self.orderbooks[pair], order_id)
        return order_id

    def limit_order(self, pair, type_, amount, price, ttl):
        '''
        @param pair: Market.
        @param type_: buy/sell.
        @param amount: The number of tokens to buy/sell.
        @param price: Maximum acceptable value for buy, minimum for sell.
        @param ttl: Time-to-live.
        '''
        order = LimitOrder(amount=amount, price=price, ttl=ttl)
        return _spawn_order(order)

    def market_order(self, pair, type_, amount, ttl):
        '''
        @param pair: Market
        @param type_: buy/sell
        @param amount: The number of tokens to buy/sell
        @param ttl: Time-to-live.
        '''
        order = MarketOrder(amount=amount, ttl=ttl)
        return _spawn_order(order)

    def get_order_status(self, pair, order_id):
        self.orderbooks[pair].get_order_status(order_id)

    def cancel_order(self, order_id):
        self.orderbooks[pair].cancel_order(order_id)


if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 8080), app,
                        handler_class=WebSocketHandler)
    server.serve_forever()
