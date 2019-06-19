from enum import Enum


from eth_utils import int_to_big_endian

from raidex.raidex_node.architecture.event_architecture import dispatch_events

from raidex.utils import pex
from raidex.utils.timestamp import to_str_repr, time_plus
from raidex.utils.random import create_random_32_bytes_id
from raidex.raidex_node.commitment_service.events import CommitEvent, CommitmentProvedEvent, ReceivedInboundEvent, CancellationRequestEvent


class TraderRole(Enum):
    MAKER = 0
    TAKER = 1


class OfferType(Enum):
    BUY = 0
    SELL = 1

    @classmethod
    def opposite(cls, type_):
        return OfferType((type_.value + 1) % 2)


class BasicOffer:

    def __init__(self, offer_id, offer_type, base_amount, quote_amount, timeout_date):
        self.offer_id = offer_id
        self.type = offer_type
        self.base_amount = base_amount
        self.quote_amount = quote_amount
        self.timeout_date = timeout_date

    @property
    def price(self):
        return float(self.quote_amount) / self.base_amount

    def __repr__(self):
        return "Offer<pex(id)={} amount={} price={} type={} timeout={}>".format(
            pex(int_to_big_endian(self.offer_id)),
            self.base_amount,
            self.price,
            self.type,
            to_str_repr(self.timeout_date))

    def __eq__(self, other):
        if not isinstance(other, BasicOffer):
            return False
        if not self.offer_id == other.offer_id:
            return False
        if not self.type == other.type:
            return False
        if not self.base_amount == other.base_amount:
            return False
        if not self.quote_amount == other.quote_amount:
            return False
        if not self.timeout_date == other.timeout_date:
            return False
        return True


class Offer(BasicOffer):

    def __init__(self, offer_id, offer_type, base_amount, quote_amount, timeout_date, trader_role):
        super(Offer, self).__init__(offer_id, offer_type, base_amount, quote_amount, timeout_date)
        self.trader_role = trader_role
        self.proof = None

    @property
    def buy_amount(self):
        if self.is_buy():
            return self.base_amount
        return self.quote_amount

    @property
    def sell_amount(self):
        if self.is_buy():
            return self.quote_amount
        return self.base_amount

    def is_maker(self):
        if self.trader_role == TraderRole.MAKER:
            return True
        return False

    def is_buy(self):
        if self.type == OfferType.BUY:
            return True
        return False

    def is_sell(self):
        return not self.is_buy()

    @property
    def has_proof(self):
        if self.proof:
            return True
        return False

    def on_enter_unproved(self):
        dispatch_events([CommitEvent(offer=self)])

    def set_proof(self, proof):
        self.proof = proof

    def on_enter_published(self):
        dispatch_events([CommitmentProvedEvent(offer=self)])

    def initiate_refund(self, raiden_event):
        dispatch_events([ReceivedInboundEvent(offer=self, raiden_event=raiden_event)])

    def on_enter_cancellation(self):
        dispatch_events([CancellationRequestEvent(offer=self)])

    def log_state(self, *args):
        if hasattr(self, 'state'):
            print(f'Offer {self.offer_id} - State Changed to: {self.state}')
        if hasattr(self, 'status'):
            print(f'Status: {self.status}')


class OfferFactory:

    @staticmethod
    def create_offer(offer_type, base_amount, quote_amount, offer_lifetime, trader_role):
        new_offer_id = create_random_32_bytes_id()
        timeout_date = time_plus(seconds=offer_lifetime)
        offer_model = Offer(new_offer_id,
                            offer_type,
                            base_amount,
                            quote_amount,
                            timeout_date,
                            trader_role)
        from raidex.raidex_node.order import fsm_offer
        fsm_offer.add_model(offer_model)
        return offer_model

    @staticmethod
    def create_from_basic(offer, trader_role):

        offer_model = Offer(offer.offer_id,
                            offer.type,
                            offer.base_amount,
                            offer.quote_amount,
                            offer.timeout_date,
                            trader_role)
        from raidex.raidex_node.order import fsm_offer
        fsm_offer.add_model(offer_model)
        return offer_model





