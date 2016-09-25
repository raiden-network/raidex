from rex.gen_orderbook_mock import gen_orderbook


class Currency():
    '''
    XXX: receive amount as int or Real?
    '''
    def __init__(self, amount):
        self.amount = amount

    @property
    def amount(amount):
        self.amount = amount


class BTC(Currency):
    def __init__(self, amount):
        Currency.__init__(self, amount)


class ETH(Currency):
    def __init__(self, amount):
        Currency.__init__(self, amount)

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



class OrderBook():

    def __init__(self):
        self.orders = list()

    def exchange(self, sell, buy):
        self.orders.append((sell, buy))

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
        return iter(self.orders)

    def __len__(self):
        return len(self.orders)
