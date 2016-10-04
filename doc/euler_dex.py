"""
Based on an idea by Nick Johnson
https://www.reddit.com/r/ethereum/comments/54l32y/euler_the_simplest_exchange_and_currency/
Modification: using linear price increase.


Exchange should probably have some way to specify the minimum number of tokens
you are willing to accept due to price changes.

And there does not seem to be any way to sell tokens to the exchange :)

"""
import math


class TokenAccount(object):
    """
    The quantity of Euler a user gets for selling a token to the exchange depends on the
    number of tokens the exchange already holds of that type.

    The cost of the nth Euler (counting from zero) is n.
    So the first Euler issued costs 1 token, the second 2 tokens, the third 3, and so forth.
    """

    def __init__(self, name):
        self.name = name
        self.num_tokens = 0  # asset: num tokens
        self.num_eulers = 0  # liabilities: euler outstanding

    def __repr__(self):
        return "<Account('%s' num_tokens=%r num_eulers=%r price=%r EUL>" % \
            (self.name.upper(), self.num_tokens, self.num_eulers, self.price_token)

    @property
    def price_euler(self):
        "price of one additional euler (in num tokens)"
        return self.quote_euler(num_eulers=1)

    @property
    def price_token(self):
        "price of one token (in num euler)"
        return 1 / self.price_euler

    def quote_euler(self, num_eulers=1):
        "returns the number of tokens required to buy num_eulers"
        pre_num = self.num_eulers
        post_num = self.num_eulers + num_eulers
        pre_integral = 0.5 * pre_num ** 2
        post_integral = 0.5 * post_num ** 2
        return (post_integral - pre_integral)  # number of tokens

    def quote_token(self, num_tokens=1):
        "returns the number of euler required to buy num_tokens"
        return (2 * num_tokens + self.num_eulers**2)**0.5 - self.num_eulers

    def sell_tokens(self, num_tokens):
        "tokens sold to the exchange, Eulers generated"
        num_eulers = self.quote_token(num_tokens)
        assert num_eulers > 0
        self.num_eulers += num_eulers
        self.num_tokens += num_tokens
        return num_eulers  # credited

    buy_eulers = sell_tokens

    def buy_tokens(self, num_eulers):
        "tokens bought from the exchange, Eulers destroyed"
        assert num_eulers <= self.num_eulers
        num_tokens = self.quote_euler(num_eulers)
        assert num_tokens <= self.num_tokens, (num_tokens, self.num_tokens)
        self.num_eulers -= num_eulers
        self.num_tokens -= num_tokens
        return num_tokens


class TokenAccountE(TokenAccount):
    """
    The quantity of Euler a user gets for selling a token to the exchange depends on the
    number of tokens the exchange already holds of that type.

    The cost of the nth Euler (counting from zero) is n.
    So the first Euler issued costs 1 token, the second 2 tokens, the third 3, and so forth.
    """

    def quote_euler(self, num_eulers=1):
        "returns the number of tokens required to buy num_eulers"
        pre_num = self.num_eulers
        post_num = self.num_eulers + num_eulers
        a = 1 / (pre_num + 1) * math.e ** (pre_num + 1)
        b = 1 / (post_num + 1) * math.e ** (post_num + 1)
        return b - a  # number of tokens

    def quote_token(self, num_tokens=1):
        "returns the number of euler required to buy num_tokens"
        """
        n = log(e*t - t + 1) - 1  # value of the first t tokens in eulers
        nd = log(e*(a+b) - (a+b) + 1) - log(e*a - a + 1)
        nd = log(e*(a+b) - (a+b) + 1) - log(e*a - a + 1)
        """
        a = self.num_tokens
        b = self.num_tokens + num_tokens
        return math.log(math.e * (a + b) - (a + b) + 1) - math.log(math.e * a - a + 1)


class Exchange(object):

    def __init__(self):
        self.token_by_name = dict()

    def add_token_account(self, ta):
        self.token_by_name[ta.name] = ta

    @property
    def num_eulers(self):
        return sum(a.num_eulers for a in self.token_by_name.values())

    def price(self, ask_token_name, bid_token_name=None, num_bid_tokens=1):
        "returns bid_tokens/ask_tokens, bid defaulting to Euler"
        ask_account = self.token_by_name[ask_token_name]
        if not bid_token_name:
            assert num_bid_tokens == 1
            return ask_account.price_token()  # the number of eulers for one token
        bid_account = self.token_by_name[bid_token_name]
        num_eulers = bid_account.quote_token(num_bid_tokens)
        num_ask_tokens = ask_account.quote_euler(num_eulers)
        return num_bid_tokens / num_ask_tokens

    def exchange(self, bid_token_name, bid_amount, ask_token_name):
        bid_account = self.token_by_name[bid_token_name]
        ask_account = self.token_by_name[ask_token_name]

        # sell tokens to the exchange
        num_eulers = bid_account.sell_tokens(bid_amount)

        # buy tokens from the exchange
        num_ask_tokens = ask_account.buy_tokens(num_eulers)
        return num_ask_tokens


def test_token():
    t = TokenAccount('any')
    assert t.quote_euler(num_eulers=1.) == (1. - 0) / 2
    t.num_eulers = 2
    n_tokens = t.quote_euler(num_eulers=1.)
    assert n_tokens == (9. - 4.) / 2
    assert t.quote_token(n_tokens) == 1.


def test_token_prices():
    t = TokenAccount('any')
    for i in range(8):
        nt = t.quote_euler(num_eulers=1.)
        ne = t.sell_tokens(nt)
        assert ne == 1.
        print i, nt, t.num_eulers, t.num_tokens, t.num_tokens / t.num_eulers

"""
def sqrt(x):
    z = (x + 1) / 2
    y = x
    i = 0
    while (z < y):
        y = z
        z = (x / z + z) / 2
        i += 1
    return y, i

for x in (4., 2312312., 752624562.2565):
    print sqrt(x)


def e2t(x):
    return 1 / (x + 1) * math.e ** (x + 1)


def t2e(x):
    return math.log(math.e * x - x + 1) - 1

x = .5
nt = e2t(x)
ne = t2e(nt)
print nt, ne
assert ne == x
"""


def test_tokenE():
    t = TokenAccountE('any')
    t.num_eulers = 10
    t.num_tokens = 10
    # buy an euler w/ tokens
    nt = t.quote_euler(num_eulers=1.)
    ne = t.sell_tokens(nt)
    print nt, ne, t.num_tokens, t.num_eulers

    # sell an euler for tokens
    ne2 = t.quote_token(num_tokens=nt)
    nes = t.buy_tokens(ne)
    print ne2, nes, t.num_tokens, t.num_eulers

    assert False


def test_exchange():
    ex = Exchange()
    a_eth = TokenAccount('eth')
    ex.add_token_account(a_eth)
    a_mkr = TokenAccount('mkr')
    ex.add_token_account(a_mkr)

    # scenario: 1 mkr == 2 eth
    # we want 1000 outstanding euler
    # we sell mkr for 333 euler
    # we sell eth for 666 euler

    # num_mkr_tokens = a_mkr.tokens_for_euler(3)
    # num_eth_tokens = a_eth.tokens_for_euler(6)
    # print num_mkr_tokens, num_eth_tokens
    # a_mkr.sell_tokens(num_mkr_tokens)
    # a_eth.sell_tokens(num_eth_tokens)

    # initial distribution after auction
    num_bought_tokens = 100

    a_mkr.num_tokens = num_bought_tokens / 3.
    a_mkr.num_eulers = a_mkr.price_token * a_mkr.num_tokens

    a_eth.num_tokens = num_bought_tokens - a_mkr.num_tokens
    a_eth.num_eulers = a_eth.price_token * a_eth.num_tokens

    print a_mkr
    print a_eth

    eth_mkr = ex.price(ask_token_name='mkr', bid_token_name='eth', num_bid_tokens=1)
    print 'eth/mkr:', eth_mkr

    #################################################
    mkr_eth = ex.price(ask_token_name='eth', bid_token_name='mkr', num_bid_tokens=1)
    print 'exchanging 1 mkr for eth @ {} mkr/eth'.format(mkr_eth)
    # User: Bid: 1 mkr Ask: eth
    # exchange: buys mkr, sells eth
    # exchange: buys mkr tokens (received) for euler (created)
    # exchange: sells eth (send) tokens for euler (received + destroyed)

    mkr_pre_eulers = a_mkr.num_eulers
    mkr_pre_tokens = a_mkr.num_tokens
    mkr_pre_price = a_mkr.price_token
    eth_pre_eulers = a_eth.num_eulers
    eth_pre_tokens = a_eth.num_tokens
    eth_pre_price = a_eth.price_token

    eth_tokens_expected = 1 / mkr_eth
    eth_tokens_received = ex.exchange(bid_token_name='mkr', bid_amount=1., ask_token_name='eth')
    assert eth_tokens_expected == eth_tokens_received
    print a_mkr
    print a_eth

    # comparing pre and post situation

    assert mkr_pre_eulers + eth_pre_eulers == a_mkr.num_eulers + a_eth.num_eulers

    assert mkr_pre_eulers < a_mkr.num_eulers  # new eulers created, exchanged for mkr tokens recvd
    assert mkr_pre_tokens < a_mkr.num_tokens  # new mkr tokens received
    assert mkr_pre_price > a_mkr.price_token  # the price of mkr/eul should drop as there is more
    assert eth_pre_eulers > a_eth.num_eulers  # eth_eulers have been destroyed
    assert eth_pre_tokens > a_eth.num_tokens  # eth has been bought, thus reduced
    assert eth_pre_price < a_eth.price_token  # the price of eth/eul should rise as there is less


if __name__ == '__main__':
    # test_token_prices()
    # test_tokenE()
    test_token()
    test_exchange()
