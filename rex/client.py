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

    def __init__(self, raiden, order_manager, commitment_manager):
        self.raiden = raiden
        self.commitment_manager = commitment_manager
        self.order_manager = order_manager

    @property
    def assets(self):
        raise NotImplementedError
        # returns assets and balances tradeable from raiden
        # requirement: have an open channel + deposit for that asset
        #TODO: get from the raiden instance

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
        """
            cs = <commitment service ethereum address>
            offer = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id])
            offer_sig = sign(sha3(offer), maker)
            commitment = rlp([sha3(offer), amount, timeout])
            commitment_sig = sign(sha3(commitment), maker)
            commitment_proof = sign(commitment_sig, cs)
        """

        raise NotImplementedError
        #TODO: send signed maker commitment message and wait for signed answer from CS

        offer = get_offer_from_id(offer_id)
        bid_token, ask_token = offer.asset_pair
        offer_msg = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id])
        offer_msg_sig = sign(sha3(offer), maker)
        commitment_msg = rlp([sha3(offer), amount, timeout])
        commitment_msg_sig = sign(sha3(commitment), maker)
        self.send_msg(commitment_service_address, commitment_msg, commitment_msg_sig)
        if successful:
            self.notify_success(commitment_service_address, offer_id)
            signed_commitment = True
            return signed_commitment
        else:
            return False

    def notify_success(self, commitment_service_address, offer_id):
        raise NotImplementedError

    def make_commitment_deposit(self, commitment_service_address, deposit_amount):
        if commitment_service_address not in self.commitment_services:
            # TODO: make raiden work with ether deposits
            asset_address = sha3('ETH') # XXX mock asset_address for now
            self.raiden.api.open(asset_address, commitment_service_address)
            successful = self.raiden.deposit(asset_address, commitment_service_address, deposit_amount)
            # assert isinstance(successful, NettingChannel)
            # TODO improve success checking
            if successful:
                self.commitment_services[commitment_service_address] = dict(balance=deposit_amount)
                return True
            else:
                return False
        else:
            successful = self.raiden.deposit(asset_address, commitment_service_address, deposit_amount)
            # assert isinstance(successful, NettingChannel)
            # TODO improve success checking
            if successful:
                self.commitment_services[commitment_service_address][balance] += deposit_amount
                return True
            else:
                return False
            # returns raiden receipt


class Currency(object):
    # TODO: add all supported currencies...
    ETH = 0
    BTC = 1


class Order(object):

    SELL = 0
    BUY = 1

    def __init__(self, type_, amount, order_id=None, ttl=600):
        self.order_id = order_id
        self.type_ = type_
        self.amount = amount
        # TODO: add removal of expired orders
        self.timeout = time.time() + ttl


class LimitOrder(Order):

    def __init__(self, amount, price, order_id=None, ttl=600, type_=Order.BUY):
        super(LimitOrder, self).__init__(amount=amount, order_id=order_id, ttl=ttl, type_=type_)
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

    def __init__(self, amount, order_id=None, ttl=600, type_=Order.BUY):
        super(MarketOrder, self).__init__(amount=amount, order_id=order_id, ttl=ttl, type_=type_)

    def __cmp__(self, other):
        if self.timeout == other.timeout and self.order_id == other.order_id:
            return 0
        elif self.timeout < other.timeout or (
                self.timeout == other.timeout and self.order_id < other.order_id):
            return -1
        else:
            return 1


class OfferView(object):

    def __init__(self, manager, pair):
        self.pair = pair
        self.orders = FastRBTree()
        self.offer_by_id = dict()
        self.manager = manager

    def add_offer(self, offer_message):
        # TODO: using mock format, must define offer_message
        message_type = offer_message['message_type']
        type_ = Order.BUY if offer_message['type'] == 'buy' else Order.SELL
        amount = offer_message['amount']
        price = offer_message.get('price')
        ttl = offer_message.get('ttl')

        if message_type == 'limit':
            order = self.manager.limit_order(pair=self.pair, type_=type_, amount=amount, price=price, ttl=ttl)
        else:
            order = self.manager.market_order(pair=self.pair, type_=type_, amount=amount, ttl=ttl)

        self.orders.insert(order, order)
        self.offer_by_id[order.order_id] = order

        return order.order_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_by_id:
            order = self.offer_by_id[offer_id]
            self.orders.remove(order)
            del self.offer_by_id[offer_id]
            # TODO: publish removal?

    def get_offer_by_id(self, offer_id):
        return self.offer_by_id.get(offer_id)

    def __len__(self):
        return len(self.orders)

    def __iter__(self):
        return iter(self.orders)


class OrderBook(object):

    def __init__(self, manager, asset_pair):
        self.manager = manager
        self.manager.add_orderbook(asset_pair, self)

        self.bids = OfferView(manager, asset_pair)
        self.asks = OfferView(manager, asset_pair)

        # TODO: offerviews should come from ClientService?
        #ask_currency, bid_currency = asset_pair
        #self.asks = get_orderbook_by_asset_pair(ask_currency, bid_currency)
        #assert isinstance(self.asks, OfferView)
        #assert self.asks.currencypair == (ask_currency, bid_currency)
        #self.bids = get_orderbook_by_asset_pair(bid_currency, ask_currency)# cpair = (BTC/ETH)
        #assert isinstance(self.bids, OfferView)
        #assert self.bids.currencypair == (bid_currency, ask_currency)

    def add(self, address, price, amount, timeout):
        id_ = sha3(address + str(price * amount))
        self.ordersindex.insert(price)
        assert id_ not in self.orders
        self.orders[id_] = (address, price, amount, timeout)

    def get_order_by_id(self, order_id):
        order = self.bids.get_offer_by_id(order_id)
        if order is None:
            order = self.asks.get_offer_by_id(order_id)
        return order

    # @property
    # def bids(self): # TODO: implement __iter__() and next() for the data structure chosen for list() representation
    #     assert len(self.orders) % 2 == 0
    #     half_list = int(len(self.orders) / 2)
    #     return reversed(self.orders[:half_list])

    # @property
    # def asks(self):
    #     assert len(self.orders) % 2 == 0
    #     half_list = int(len(self.orders) / 2)
    #     return self.orders[half_list:]

    def set_manager(self, manager):
        self.manager = manager

    def insert(self, order):
        if order.type_ == Order.BUY:
            self.asks.add_offer(order)
        else:
            self.bids.add_offer(order)

    def get_order_status(self, order_id):
        pass

    def cancel_order(self, order_id):
        self.bids.remove_offer(order_id)
        self.asks.remove_offer(order_id)

    def __repr__(self):
        return "BookOrder<bids={} asks={}>".format(len(self.bids), len(self.asks))


class OrderTask(gevent.Greenlet):

    def __init__(self, orderbook, order):
        super(OrderTask, self).__init__()
        self.orderbook = orderbook
        self.order = order
        self.stop_event = gevent.event.AsyncResult()

    def _run(self):  # pylint: disable=method-hidden
        stop = None

        offers = self.orderbook.asks
        total_amount = total_price = 0
        remaining = self.order.amount
        orders_to_buy = []
        while stop is None:
            for offer in offers:
                if offer.price <= self.order.price:
                    amount = min(remaining, offer.amount)
                    total_amount += amount
                    total_price += amount * offer.price
                    remaining -= amount
                    orders_to_buy.append((offer, amount))
                    if total_amount == self.order.amount:
                        self._try_buy_operation(orders_to_buy)
                        break
            total_amount = total_price = 0
            remaining = self.order.amount
            orders_to_buy = []
            #stop = self.stop_event.wait(0)
            gevent.sleep(1)

    def _try_buy_operation(self, orders_with_amount):
        print("Will try to buy: {}".format(
            " + ".join("{}*{}={}".format(
                order_with_amount[0].price,
                order_with_amount[1],
                order_with_amount[0].price * order_with_amount[1])
                for order_with_amount in orders_with_amount)))

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

    def limit_order(self, pair, type_, amount, price, ttl):
        '''
        @param pair: Market.
        @param type_: buy/sell.
        @param amount: The number of tokens to buy/sell.
        @param price: Maximum acceptable value for buy, minimum for sell.
        @param ttl: Time-to-live.
        '''
        order = LimitOrder(amount=amount, price=price, ttl=ttl, type_=type_)
        order.order_id = self.get_next_id()
        order.task = None
        if type_ == Order.BUY:
            order.task = OrderTask(self.orderbooks[pair], order)
            order.task.start()
        return order

    def market_order(self, pair, type_, amount, ttl):
        '''
        @param pair: Market
        @param type_: buy/sell
        @param amount: The number of tokens to buy/sell
        @param ttl: Time-to-live.
        '''
        order = MarketOrder(amount=amount, ttl=ttl, type_=type_)
        order.order_id = self.get_next_id()
        order.task = None
        if type_ == Order.BUY:
            order.task = OrderTask(self.orderbooks[pair], order)
            order.task.start()
        return order

    def get_order_status(self, pair, order_id):
        self.orderbooks[pair].get_order_status(order_id)

    def cancel_order(self, order_id):
        self.orderbooks[pair].cancel_order(order_id)


if __name__ == "__main__":
    server = WSGIServer(("0.0.0.0", 8080), app,
                        handler_class=WebSocketHandler)
    server.serve_forever()
