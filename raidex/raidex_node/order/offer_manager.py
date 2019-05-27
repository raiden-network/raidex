import structlog

from raidex.raidex_node.order.offer import OfferFactory, TraderRole
from raidex.raidex_node.order.limit_order import LimitOrder

logger = structlog.get_logger('OfferManager')


class OfferManager:

    __slots__ = [
        'offers',
        'event_queue',
        'commitment_service_queue',
        'message_broker_queue'
    ]

    def __init__(self):
        self.offers = {}

    def add_offer(self, offer):
        self.offers[offer.offer_id] = offer

    def has_offer(self, offer_id):
        return offer_id in self.offers

    def get_offer(self, offer_id):
        return self.offers[offer_id] if offer_id in self.offers else None

    def create_take_offer(self, offer):
        take_offer = OfferFactory.create_from_basic(offer, TraderRole.TAKER)

        self.offers[take_offer.offer_id] = take_offer
        logger.info(f'New Take Offer: {take_offer.offer_id}')
        return take_offer

    def create_make_offer(self, order: LimitOrder, amount_left):

        new_offer = OfferFactory.create_offer(offer_type=order.order_type,
                                              base_amount=amount_left,
                                              quote_amount=int(amount_left * order.price),
                                              offer_lifetime=order.lifetime,
                                              trader_role=TraderRole.MAKER)

        self.offers[new_offer.offer_id] = new_offer

        logger.info(f'New Offer: {new_offer.offer_id}')
        return new_offer







