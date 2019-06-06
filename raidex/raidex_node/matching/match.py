
from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.order.offer import Offer, TraderRole
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.trader.events import SwapInitEvent
from raidex.raidex_node.trader.listener.events import ExpectInboundEvent
from datetime import datetime


class Match:

    class TargetData:

        def __init__(self, target, commitment_proof):
            self.target = target
            self.commitment_proof = commitment_proof

        @property
        def address(self):
            return self.target

    def __init__(self, offer: Offer, trader_role: TraderRole, commitment, commitment_proof):
        self.offer = offer
        self.trader_role = trader_role
        self.target_data = Match.TargetData(commitment, commitment_proof)
        self.match_time = datetime.utcnow()

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

    def received_inbound(self, raiden_event):
        self.offer.received_inbound(raiden_event)
        self.completed()

    def completed(self):
        print(datetime.utcnow() - self.match_time)

    @property
    def target(self):
        return self.target_data.address

    def get_secret(self):
        return self.target_data.commitment_proof.secret

    def get_secret_hash(self):
        return self.target_data.commitment_proof.secret_hash

    def on_enter_exchanging(self):
        dispatch_events([SwapInitEvent(self), ExpectInboundEvent(self.target, self.offer.offer_id)])


class MatchFactory:

    @staticmethod
    def maker_match(offer, target, commitment_proof):
        return Match(offer, TraderRole.MAKER, target, commitment_proof)

    @staticmethod
    def taker_match(offer, offer_entry):
        return Match(offer, TraderRole.TAKER, offer_entry.initiator, offer_entry.commitment_proof)
