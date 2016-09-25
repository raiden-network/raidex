from collections import deque


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


class OrderBook():

    def __init__(self):
        self.orders = list()

    def exchange(self, sell, buy):
        self.orders.append((sell, buy))

    def __iter__(self):
        return iter(self.orders)

    def __len__(self):
        return len(self.orders)
