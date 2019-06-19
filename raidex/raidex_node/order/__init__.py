__all__ = ['offer', 'fsm_offer', 'limit_order']

from transitions.extensions.nesting import NestedState
from transitions.extensions import HierarchicalMachine as Machine

from raidex.raidex_node.order.offer import Offer

ENTER_UNPROVED = Offer.on_enter_unproved.__name__
ENTER_PUBLISHED = Offer.on_enter_published.__name__
ENTER_PROVED = Offer.set_proof.__name__
ENTER_CANCELLATION = Offer.on_enter_cancellation.__name__
ENTER_WAIT_FOR_REFUND = Offer.initiate_refund.__name__
AFTER_STATE_CHANGE = Offer.log_state.__name__


class OfferMachine(Machine):

    def set_state(self, state, model=None):
        super(OfferMachine, self).set_state(state, model)
        if isinstance(state, str):
            state = self.get_state(state)
        model.status = state.parent.name if state.parent else state.name


class OfferState(NestedState):

    def __repr__(self):
        return self.name

    @property
    def initial(self):
        if len(self.children) > 0:
            return self.children[0]
        return None

    def name(self):
        return self._name


OPEN = OfferState('open')
OPEN_CREATED = OfferState('created', parent=OPEN)
OPEN_UNPROVED = OfferState('unproved', on_enter=[ENTER_UNPROVED], parent=OPEN)
OPEN_PROVED = OfferState('proved', on_enter=[ENTER_PROVED], parent=OPEN)
OPEN_PUBLISHED = OfferState('published', on_enter=[ENTER_PUBLISHED], parent=OPEN)
OPEN_CANCELLATION_REQUESTED = OfferState('cancellation_requested', on_enter=[ENTER_CANCELLATION], parent=OPEN)

PENDING = OfferState('pending')
PENDING_EXCHANGING = OfferState('exchanging', parent=PENDING)
PENDING_WAIT_FOR_REFUND = OfferState('wait_for_refund', on_enter=[ENTER_WAIT_FOR_REFUND], parent=PENDING)

COMPLETED = OfferState('completed')
CANCELED = OfferState('canceled')


OFFER_STATES = [
    OPEN,
    PENDING,
    CANCELED,
    COMPLETED,
]

TRANSITIONS = [

    {'trigger': 'initiating',
     'source': OPEN_CREATED,
     'dest': OPEN_UNPROVED},
    {'trigger': 'payment_failed',
     'source': OPEN_UNPROVED,
     'dest': OPEN_UNPROVED},
    {'trigger': 'timeout',
     'source': OPEN,
     'dest': OPEN_CANCELLATION_REQUESTED},
    {'trigger': 'receive_cancellation_proof',
     'source': OPEN,
     'dest': CANCELED},
    {'trigger': 'receive_commitment_proof',
     'source': OPEN_UNPROVED,
     'dest': OPEN_PROVED},
    {'trigger': 'received_offer',
     'source': OPEN_PROVED,
     'dest': OPEN_PUBLISHED},
    {'trigger': 'found_match',
     'source': OPEN_PUBLISHED,
     'dest': PENDING_EXCHANGING},
    {'trigger': 'found_match',
     'source': OPEN_PROVED,
     'dest': PENDING_EXCHANGING},
    {'trigger': 'received_inbound',
     'source': PENDING_EXCHANGING,
     'dest': PENDING_WAIT_FOR_REFUND},
    {'trigger': 'received_inbound',
     'source': PENDING_WAIT_FOR_REFUND,
     'dest': COMPLETED},
]

fsm_offer = OfferMachine(states=OFFER_STATES,
                         transitions=TRANSITIONS,
                         initial=OPEN,
                         after_state_change=AFTER_STATE_CHANGE)

