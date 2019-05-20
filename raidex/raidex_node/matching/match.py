
from raidex.raidex_node.architecture.event_architecture import dispatch_events

from raidex.raidex_node.order.offer import Offer, TraderRole
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.trader.events import SwapInitEvent


class Match:

    class TargetData:

        def __init__(self, commitment, commitment_proof):
            self.commitment = commitment
            self.commitment_proof = commitment_proof

        @property
        def address(self):
            return self.commitment.sender

    def __init__(self, offer: Offer, trader_role: TraderRole, commitment, commitment_proof):
        self.offer = offer
        self.trader_role = trader_role
        self.target_data = Match.TargetData(commitment, commitment_proof)

    def is_maker(self):
        if self.trader_role == TraderRole.MAKER:
            return True
        return False

    def is_taker(self):
        return not self.is_maker()

    def get_send_amount(self):
        if self.is_maker() and self.offer.is_buy() or self.is_taker() and self.offer.is_sell():
            return self.offer.quote_amount
        return self.offer.base_amount

    def get_token_from_market(self, market: TokenPair):
        if self.is_maker() and self.offer.is_buy() or self.is_taker() and self.offer.is_sell():
            return market.checksum_quote_address
        return market.checksum_base_address

    def matched(self):
        self.offer.found_match()
        self.on_enter_exchanging()

    @property
    def target(self):
        return self.target_data.commitment.sender

    def get_secret(self):
        return self.target_data.commitment_proof.secret

    def get_secret_hash(self):
        return self.target_data.commitment_proof.secret_hash

    def on_enter_exchanging(self):
        dispatch_events([SwapInitEvent(self)])


class MatchFactory:

    @staticmethod
    def maker_match(offer_entry):
        Match(offer_entry.offer, TraderRole.MAKER)

    @staticmethod
    def taker_match(offer, offer_entry):
        return Match(offer, TraderRole.TAKER, offer_entry.commitment, offer_entry.commitment_proof)
