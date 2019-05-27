__all__ = ['offer', 'fsm_offer', 'limit_order']

from transitions import State, Machine

from raidex.raidex_node.order.offer import Offer

ENTER_UNPROVED = Offer.on_enter_unproved.__name__
ENTER_PUBLISHED = Offer.on_enter_published.__name__
ENTER_PROVED = Offer.set_proof.__name__
ENTER_WAIT_FOR_REFUND = Offer.initiate_refund.__name__

OFFER_STATES = [
    State('created'),
    State('unproved', on_enter=[ENTER_UNPROVED]),
    State('proved', on_enter=[ENTER_PROVED]),
    State('published', on_enter=[ENTER_PUBLISHED]),
    State('exchanging'),
    State('wait_for_refund', on_enter=[ENTER_WAIT_FOR_REFUND]),
    State('completed'),
    State('cancelled'),
]
TRANSITIONS = [

    {'trigger': 'initiating',
     'source': 'created',
     'dest': 'unproved'},
    {'trigger': 'payment_failed',
     'source': 'unproved',
     'dest': 'unproved'},
    {'trigger': 'timeout',
     'source': ['unproved', 'proved', 'published'],
     'dest': 'cancelled'},
    {'trigger': 'receive_commitment_proof',
     'source': 'unproved',
     'dest': 'proved'},
    {'trigger': 'received_offer',
     'source': 'proved',
     'dest': 'published'},
    {'trigger': 'found_match',
     'source': 'published',
     'dest': 'exchanging'},
    {'trigger': 'found_match',
     'source': 'proved',
     'dest': 'exchanging'},
    {'trigger': 'timeout',
     'source': 'exchanging',
     'dest': 'exchanging'},
    {'trigger': 'timeout',
     'source': 'completed',
     'dest': 'completed'},
    {'trigger': 'received_inbound',
     'source': 'exchanging',
     'dest': 'wait_for_refund'},
    {'trigger': 'received_inbound',
     'source': 'wait_for_refund',
     'dest': 'completed'},
]


fsm_offer = Machine(states=OFFER_STATES, transitions=TRANSITIONS, initial='created', after_state_change='log_state')

