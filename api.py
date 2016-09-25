
class API(object):

    def __init__(self):
        pass

    def exchange(bid_asset, ask_asset, quantity, price, time_valid, callback=None):
        if price:
            #  Limit order
            #  price: maximum price, time_valid: time the limit order is valid
            pass
        else:
            # Market order
            # time_valid:   time the order is valid and tries to buy assets for the lowest available price
            #               until the quantity is reached
            pass


    def poll_orderbook(bid_asset, ask_asset, connected=False, filter=None):
        # XXX this orderbook probably shouldn't contain the broadcasted asset swap requests, but the actual higher level Market Order and Limit Order request ?
        if connected is True:
            # query for the local orderbook, used for gathering market information and having a global view of the network
            # it's not required to have bid_asset or ask_asset available here
        else:
            # query for the global orderbook, only showing the orders that are exchanged on trusted parties the client has an open connection to
            if bid_asset not in available_assets:
                return None, None

        bids = [(None,None,None)] # [(price,timestamp,quantity),..,(price,timestamp,quantity)]
        # `bids` consists of a list of tuples, containing the timestamp, bid_asset quantity of the order and the price in ask_asset
        # the list is ordered by price (lowest to highest), then timestamp (earliest to oldest)
        asks = [(None,None,None)] # ()
        # `asks` consists of a list of tuples, containing the timestamp, ask_asset quantity of the order and the price in bid_asset
        # the list is ordered by price (lowest to highest), then timestamp (earliest to oldest)
        return bids, asks
