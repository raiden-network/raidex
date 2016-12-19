import gevent

class OrderTask(gevent.Greenlet):
    """
    Spawns ExchangeTasks, in order to fill the user-initiated Order 'completely' (to be discussed)
    The OrderTask will first try to buy available Offers that match the market, desired price and don't exceed the amount.
    If the Order isn't filled after that, it will spawn MakerExchangeTasks to publish offers with a reversed asset_pair
    """

    def __init__(self, pair, type_, amount, price, ttl):
        pass