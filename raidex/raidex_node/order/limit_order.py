from raidex.raidex_node.order.offer import OfferType
from raidex.constants import DEFAULT_OFFER_LIFETIME
from raidex.utils.random import create_random_32_bytes_id


class LimitOrder:

    __slots__ = [
        'order_id',
        'order_type',
        'amount',
        'price',
        'lifetime',
    ]

    def __init__(self, order_id, order_type: OfferType, amount: int, price: int, lifetime: int = DEFAULT_OFFER_LIFETIME):
        self.order_id = order_id
        self.order_type = order_type
        self.amount = amount
        self.price = price
        self.lifetime = lifetime

    @classmethod
    def from_dict(cls, data):

        if 'order_id' not in data:
            order_id = create_random_32_bytes_id()
        else:
            order_id = data['order_id']

        if 'lifetime' not in data:
            data['lifetime'] = DEFAULT_OFFER_LIFETIME

        if data['order_type'] == 'BUY':
            order_type = OfferType.BUY
        else:
            order_type = OfferType.SELL

        obj = cls(
            order_id,
            order_type,
            data['amount'],
            data['price'],
            data['lifetime']
        )
        return obj

