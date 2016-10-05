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

def get_mocked_orderbook_by_asset_pair(self, asset_pair):
    if asset_pair not in self.order_manager:
        # instantiate empty orderbook
        orderbook = OrderBook()
        # fill with mock data
        utils.fill_mocked_orderbook(orderbook)
        self.order_manager.add_orderbook(orderbook)
    else:
        orderbook = self.order_manager.get_order_book(asset_pair)
        orderbook.update_mocked_orderbook(orderbook)
    return orderbook

class CommitmentManager(object):

def __init__(self, raidex, cs_transport):
    self.raidex = raidex
    self.transport = cs_transport
    self.commitment_services = dict() # cs_address -> balance
    self.proofs = dict() # offer_id -> proof

def commit(self, commitment_service_address, offer_id, commitment_deposit, timeout):
    """
    offer_id == hashlock == sha3(offer.hash)

    XXX: maybe dont take the offer_id but instead the preconstructed messages.Offer and
    than hash it to the id internally
    """
    ## Initial Checks:
    # check if known CS
    assert commitment_service_address in self.commitment_services
    # check for insufficient funds
    balance = self.commitment_services[commitment_service_address]
    assert  balance >= commitment_deposit

    ## Announce the commitment to the CS:
    offer = get_offer_by_id(offer_id)  # TODO XXX where to store?
    assert isinstance(messages.Offer, offer)
    self.transport.request_commitment(commitment_service_address, offer)  # TODO
    # CS will hash offer, wait for incoming transfers and compare the hashlocks to the commitment_requests
    # TODO: wait for ACK from CS, include timeout

    ## Send the actual commitment as a raiden transfer
    if ack:
        # send a locked, direct transfer to the CS, where the hashlock == sha3(offer.hash)
        self.raidex.raiden.send_cs_transfer(commitment_service_address, deposit_amount, hashlock=offer_id)  # TODO
        # write changes to current balance
        balance -= commitment_deposit
        self.commitment_services[commitment_service_address] = balance

        ## TODO: wait for commitment_proof
        # what if transfer is received, but commitment_proof is never sent out by cs?
        # add timeout, since market price could have changed
        if commitment_proof:
            assert isinstance(messages.CommitmentProof, commitment_proof)
            self.proofs[offer_id] = commitment_proof
            commitment = get_commitment_by_id(offer_id)  # TODO XXX where to store?
            assert isinstance(messages.Commitment, commitment)
            # construct with classmethod
            proven_offer = messages.ProvenOffer.from_offer(offer, commitment, commitment_proof)

            ## Broadcast the valid, committed-to offer into the network and wait that someone takes it
            try:
                self.raidex.broadcast.post(proven_offer) # serialization is done in broadcast
            except BroadcastUnreachable:
                # TODO: rollback balance changes and put ProvenOffer in a resend queue

            return offer_id


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
    """
    Maybe this class isn't even necessary and we just use the Offer message objects
    from the broadcast?
    """

SELL = 0
BUY = 1

def __init__(self, pair,amount, price, order_id=None, ttl=600, type_=Order.BUY):
    self.pair = pair
    self.order_id = order_id
    self.type_ = type_
    self.amount = amount
    # TODO: add removal of expired orders
    self.timeout = time.time() + ttl  # TODO switch to absolute time since epoch
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

@classmethod
def from_offer_message(cls, offer_msg, compare_pair):
    msg_pair = (offer_msg.bid_token, offer_msg.ask_token)
    if msg_pair == compare_pair:
        type_ = Order.SELL #XXX checkme
        price = offer_msg.bid_amount / offer_msg.ask_amount
        amount = offer_msg.bid_amount
    if tuple(reversed(msg_pair)) == compare_pair
        type_=Order.BUY #XXX checkme
        price = offer_msg.ask_amount / offer_msg.bid_amount
        amount = offer_msg.ask_amount
    # TODO check type conversion
    order_id = sha3(offer_msg.hash)
    ttl = offer_msg.timeout
    return cls(compare_pair, amount, price, order_id, ttl, type_)


class OfferView(object):

def __init__(self, manager, pair):
    self.pair = pair
    self.orders = FastRBTree()
    self.offer_by_id = dict()
    self.manager = manager

def add_offer(self, offer):
    # type will be determined somewhere else (e.g. OfferManager),
    # and then the according OfferView gets filled

    order = offer # FIXME

    self.orders.insert(order, order)
    self.offer_by_id[order.order_id] = order

    return order.order_id

def remove_offer(self, offer_id):
    if offer_id in self.offer_by_id:
        order = self.offer_by_id[offer_id]
        self.orders.remove(order)
        del self.offer_by_id[offer_id]

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

def add_offer_from_msg(self, offer_msg):
    order = Order.from_offer_message(offer_msg, compare_pair=asset_pair)
    if order.type_ is Order.SELL:
        self.bids.add_offer(order)
    if order.type_ is Order.BUY:
        self.asks.add_offer(order)

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
