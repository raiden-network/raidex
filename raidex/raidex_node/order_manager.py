from raidex_service.raidex_node.order_task import OrderTask

class OrderManager(object):
    """
    spawns and keeps track of all the Orders that were initiated through the api
    for initiating an Order, the OrderManager will spawn an OrderTask

    """

    def __init__(self):
        self.order_tasks = dict()

    def spawn_order_task(self, pair, type_, amount, price, ttl):
        """
        @param pair: Market.
        @param type_: buy/sell.
        @param amount: The number of tokens to buy/sell.
        @param price: Maximum acceptable value for buy, minimum for sell.
        @param ttl: Time-to-live.
        """

        task = OrderTask(pair, type_, amount, price, ttl)