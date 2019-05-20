from raidex.raidex_node.offer_book import OfferBook
from raidex.raidex_node.order.limit_order import LimitOrder


class MatchingEngine:

    __slots__ = [
        'offer_book',
        'match'
    ]

    def __init__(self, offer_book: OfferBook, match):
        self.offer_book = offer_book
        self.match = match

    def initialize_matching(self, match):
        self.match = match

    def match_new_order(self, order: LimitOrder):

        matching_offer_entries, amount_left = self.match(self.offer_book, order)

        return matching_offer_entries, amount_left


