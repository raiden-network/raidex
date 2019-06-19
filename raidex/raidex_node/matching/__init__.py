__all__ = ['matching_engine']

from transitions import State, Machine



OFFER_STATES = [
    'created',
    'cancelled',
]
TRANSITIONS = [

    {'trigger': 'to_initiated',
     'source': 'created',
     'dest': 'initiated'},
    {'trigger': 'payment_failed',
     'source': 'initiated',
     'dest': 'initiated'},
    {'trigger': 'timeout',
     'source': ['initiated', 'proved', 'published'],
     'dest': 'cancelled'},
    {'trigger': 'receive_commitment_prove',
     'source': 'initiated',
     'unless': 'is_matched',
     'dest': 'proved'},
    {'trigger': 'receive_commitment_prove',
     'source': 'initiated',
     'conditions': 'is_matched',
     'dest': 'pending'},
    {'trigger': 'received_offer',
     'source': 'proved',
     'dest': 'published'},
]


fsm_offer = Machine(states=OFFER_STATES, transitions=TRANSITIONS, initial='created', after_state_change='log_state')