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
        'corresponding_offers'
    ]

    def __init__(self, order_id, order_type: OfferType, amount: int, price: int, lifetime: int = DEFAULT_OFFER_LIFETIME):
        self.order_id = order_id
        self.order_type = order_type
        self.amount = amount
        self.price = price
        self.lifetime = lifetime
        self.corresponding_offers = dict()

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

    def add_offer(self, offer):
        self.corresponding_offers[offer.offer_id] = offer
        offer.initiating()

    def cancel_order(self):

        for offer in self.corresponding_offers.values():
            offer.cancel()

    @property
    def open(self):
        for offer in self.corresponding_offers.values():
            if offer.state == 'published':
                return True
        return False

    @property
    def completed(self):
        for offer in self.corresponding_offers.values():
            if offer.state != 'completed':
                return False
        return True

    @property
    def canceled(self):
        for offer in self.corresponding_offers.values():
            if offer.state == 'cancelled':
                return True
        return False

    @property
    def amount_traded(self):
        amount_traded = 0

        for offer in self.corresponding_offers.values():
            if offer.state == 'completed':
                amount_traded += offer.base_amount
        return amount_traded

