import gevent
import time
from bintrees import FastRBTree
from bottle import request, Bottle, abort
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from rex.gen_orderbook_mock import gen_orderbook
from ethereum.utils import sha3


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

class RaidexException(Exception):
    pass

class OrderTypeMismatch(RaidexException):
    pass

class InsufficientCommitmentFunds(RaidexException):
    pass

class UnknownCommitmentService(RaidexException):
    pass

class UntradableAssetPair(RaidexException):
    pass

class ClientService(object):

    def __init__(self, raiden, order_manager, commitment_manager, api):
        self.raiden = raiden
        self.commitment_manager = commitment_manager
        self.order_manager = order_manager
        self.api = api

    @property
    def assets(self):
        # returns assets and balances tradeable from raiden
        # requirement: have an open channel + deposit for that asset
        #TODO: get from the raiden instance
        raise NotImplementedError

    def get_orderbook_by_asset_pair(self, asset_pair):
        if asset_pair not in self.order_manager.orderbooks:
            raise UntradableAssetPair
        else:
            orderbook = self.order_manager.get_order_book(asset_pair)
        return orderbook


class CommitmentManager(object):

    def __init__(self, raidex, cs_transport):
        self.raidex = raidex
        self.transport = cs_transport
        self.commitment_services = dict() # cs_address -> balance
        self.proofs = dict() # offer_id -> CommitmentProof
        self.commitments = dict()  # offer_id -> Commitment

    def commit(self, commitment_service_address, offer_id, commitment_deposit, timeout):
        """
        offer_id == hashlock == sha3(offer.hash)

        XXX: maybe dont take the offer_id but instead the preconstructed messages.Offer and
        than hash it to the id internally
        """
        ## Initial Checks:
        # check if known CS
        if commitment_service_address not in self.commitment_services:
            raise UnknownCommitmentService
        # check for insufficient funds
        balance = self.commitment_services[commitment_service_address]
        if not balance >= commitment_deposit:
            raise InsufficientCommitmentFunds

        ## Announce the commitment to the CS:
        commitment = messages.Commitment(offer_id, timeout, commitment_deposit)
        self.commitments[offer_id] = commitment
        self.transport.request_commitment(commitment_service_address, commitment)  # TODO
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
                assert isinstance(commitment_proof, messages.CommitmentProof)
                self.proofs[offer_id] = commitment_proof
                # construct with classmethod
                proven_offer = messages.ProvenOffer.from_offer(offer, commitment, commitment_proof)

                ## Broadcast the valid, committed-to offer into the network and wait that someone takes it
                try:
                    self.raidex.broadcast.post(proven_offer) # serialization is done in broadcast
                except BroadcastUnreachable:
                    # TODO: rollback balance changes and put ProvenOffer in a resend queue
                    pass

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
    ETH = 'ETH'
    BTC = 'BTC'


class OrderType(object):
    BID = 0
    ASK = 1


class Order(object):
    """
    Maybe this class isn't even necessary and we just use the Offer message objects
    from the broadcast?
    """

    def __init__(self, pair, type_, amount, price, timeout, order_id=None):
        self.pair = pair
        self.order_id = order_id
        self.type_ = type_
        self.amount = amount
        # TODO: add removal of expired orders
        self.timeout = timeout
        self.price = price

    def __cmp__(self, other):
        if self.price == other.price and self.timeout == other.timeout:
            return 0
        elif self.price < other.price or (
                self.price == other.price and self.timeout < other.timeout):
            return -1
        else:
            return 1

    def __repr__(self):
        # FIXME: check timeout coming from offer_messages
        return "Order<order_id={} amount={} price={} type={} pair={}>".format(
                self.order_id, self.amount, self.price, self.type_, self.pair)

    @classmethod
    def from_offer_message(cls, offer_msg, compare_pair):
        msg_pair = (offer_msg.bid_token, offer_msg.ask_token)
        # print msg_pair
        if msg_pair == compare_pair:
            type_ = OrderType.BID #XXX checkme
            price = float(offer_msg.bid_amount) / offer_msg.ask_amount
            amount = offer_msg.bid_amount
        if msg_pair[::-1] == compare_pair:
            type_ = OrderType.ASK #XXX checkme
            price = float(offer_msg.bid_amount) / offer_msg.ask_amount
            amount = offer_msg.ask_amount
        order_id = sha3(offer_msg.offer_id)
        return cls(compare_pair, type_, amount, price, order_id, offer_msg.timeout / 1000.0)


class OfferView(object):

    def __init__(self, pair, type_):
        self.pair = pair
        self.type_ = type_
        self.orders = FastRBTree()
        self.offer_by_id = dict()

    def add_offer(self, order):
        # type_ will be determined somewhere else (e.g. OfferManager),
        # and then the according OfferView gets filled
        assert isinstance(order, Order)
        if order.type_ != self.type_ or order.pair != self.pair:
            raise OrderTypeMismatch

        self.orders.insert(order, order)
        self.offer_by_id[order.order_id] = order

        #if self.type_ == OrderType.BID:
        #    order.task = OrderTask(self.orderbooks[pair], order)
        #    order.task.start()

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

    def __init__(self, asset_pair):
        self.asset_pair = asset_pair
        self.bids = OfferView(asset_pair, type_=OrderType.BID)
        self.asks = OfferView(asset_pair, type_=OrderType.ASK)
        self.tasks = dict()

    def insert_from_msg(self, offer_msg):
        # needs to be inserted from a message, because type_ determination is done
        # in the Order instantiation based on the compare_pair:
        # print offer_msg.bid_token
        order = Order.from_offer_message(offer_msg, compare_pair=self.asset_pair)
        if order.type_ is OrderType.BID:
            self.bids.add_offer(order)
        if order.type_ is OrderType.ASK:
            self.asks.add_offer(order)

        return order.order_id

    def run_task_for_order(self, order, callback=None):
        if not isinstance(order, Order) or order.order_id in self.tasks:
            return
        self.tasks[order.order_id] = OrderTask(self, order, callback=callback)
        self.tasks[order.order_id].start()

    def get_order_by_id(self, order_id):
        order = self.bids.get_offer_by_id(order_id)
        if order is None:
            order = self.asks.get_offer_by_id(order_id)
        return order

    def set_manager(self, manager):
        self.manager = manager

    def get_order_status(self, order_id):
        pass

    def cancel_order(self, order_id):
        self.bids.remove_offer(order_id)
        self.asks.remove_offer(order_id)

    def __repr__(self):
        return "BookOrder<bids={} asks={}>".format(len(self.bids), len(self.asks))


class FIFOMatcher(object):
    '''
    A simple FIFO matcher.
    '''
    def __init__(self, order, offers):
        self.order = order
        self.offers = offers

    def match(self):
        total_amount = total_price = 0
        remaining = self.order.amount
        orders_to_buy = []
        for offer in self.offers:
            if offer.price <= self.order.price:
                amount = min(remaining, offer.amount)
                total_amount += amount
                total_price += amount * offer.price
                remaining -= amount
                orders_to_buy.append((offer, amount))
                if total_amount == self.order.amount:
                    return orders_to_buy
        return []


class OrderTask(gevent.Greenlet):

    def __init__(self, orderbook, order, matcher=FIFOMatcher, callback=None):
        super(OrderTask, self).__init__()
        self.orderbook = orderbook
        self.order = order
        self.matcher = matcher(order, orderbook.asks)
        self.callback = callback
        self.stop_event = gevent.event.AsyncResult()

    def _run(self):  # pylint: disable=method-hidden
        stop = None

        while stop is None:
            orders_to_buy = self.matcher.match()
            if orders_to_buy and self.callback is not None:
                self.callback(orders_to_buy)
            # TODO: instead of sleeping, should wait for event signaling new offers
            stop = self.stop_event.wait(1)

    # FIXME: remove later (only useful for debug)
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
        self.trade_history = dict()
        self.order_id = 0  # increment per new order

    def add_orderbook(self, pair, orderbook):
        self.orderbooks[pair] = orderbook
        orderbook.set_manager(self)

    def get_order_book(self, pair):
        assert pair in self.orderbooks
        return self.orderbooks[pair]

    def get_trade_history(self, pair, num_trades):
        assert pair in self.trade_history
        return self.trade_history[pair]

    def limit_order(self, pair, type_, amount, price, ttl):
        '''
        @param pair: Market.
        @param type_: buy/sell.
        @param amount: The number of tokens to buy/sell.
        @param price: Maximum acceptable value for buy, minimum for sell.
        @param ttl: Time-to-live.
        '''
        order = Order(amount=amount, price=price, ttl=ttl, type_=type_)
        order.order_id = None  # FIXME
        order.task = None
        if type_ == OrderType.BID:
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
        order = Order(amount=amount, ttl=ttl, type_=type_)
        order.order_id = None  # FIXME
        order.task = None
        if type_ == OrderType.BID:
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
