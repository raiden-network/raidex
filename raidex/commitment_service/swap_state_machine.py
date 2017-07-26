import gevent
from functools import wraps
from transitions import Machine

from raidex.utils import timestamp

SWAP_BASE_STATES = [
    'initializing',
    'wait_for_maker',
    'wait_for_taker',
    'wait_for_execution',
    'wait_for_maker_execution',
    'wait_for_taker_execution',
    'traded',
    'uncommitted',
    'untraded',
    'failed',
    'processed',
]

SWAP_INITIAL_STATE = 'initializing'


def swap_setup_state_transitions(fsm, auto_spawn_timeout):
    fsm.add_transition('timeout', 'wait_for_taker', 'untraded',
                       after=[omit_args_and_kwargs(fsm.swap.refund_maker), 'finalize'])
    fsm.add_transition('timeout', ['initializing', 'wait_for_maker'], 'uncommitted',
                       after='finalize')
    fsm.add_transition('maker_commitment_msg', 'initializing', 'wait_for_maker',
                       after=[fsm.set_maker_commitment])
    fsm.add_transition('transfer_receipt', 'wait_for_maker', 'wait_for_taker',
                       conditions=[fsm.sender_is_maker],
                       after=[fsm.set_maker_transfer_receipt,
                              omit_args_and_kwargs(fsm.swap.send_maker_commitment_proof)])
    # TODO check if prepare is the right place to execute
    fsm.add_transition('taker_commitment_msg', 'wait_for_taker', '=', prepare=[fsm.queue_commitment])
    fsm.add_transition('transfer_receipt', 'wait_for_taker', 'wait_for_execution',
                       conditions=[fsm.sender_sent_taker_commitment],
                       after=[fsm.accept_taker_commitment_from_receipt, fsm.set_taker_transfer_receipt,
                              omit_args_and_kwargs(fsm.swap.send_offer_taken),
                              omit_args_and_kwargs(fsm.swap.send_taker_commitment_proof)])

    fsm.add_transition('swap_execution_msg', 'wait_for_execution', 'wait_for_taker_execution',
                       conditions=[fsm.sender_is_maker],
                       after=[fsm.set_maker_execution])

    fsm.add_transition('swap_execution_msg', 'wait_for_execution', 'wait_for_maker_execution',
                       conditions=[fsm.sender_is_taker],
                       after=[fsm.set_taker_execution])

    fsm.add_transition('swap_execution_msg', 'wait_for_taker_execution', 'traded',
                       conditions=[fsm.sender_is_taker],
                       after=[fsm.set_taker_execution,
                              omit_args_and_kwargs(fsm.swap.send_swap_completed),
                              omit_args_and_kwargs(fsm.swap.refund_maker_with_fee),
                              omit_args_and_kwargs(fsm.swap.refund_taker_with_fee),
                              'finalize'])
    fsm.add_transition('swap_execution_msg', 'wait_for_maker_execution', 'traded',
                       conditions=[fsm.sender_is_maker],
                       after=[fsm.set_maker_execution,
                              omit_args_and_kwargs(fsm.swap.send_swap_completed),
                              omit_args_and_kwargs(fsm.swap.refund_maker_with_fee),
                              omit_args_and_kwargs(fsm.swap.refund_taker_with_fee),
                              'finalize'])

    fsm.add_transition('timeout', ['wait_for_execution', 'wait_for_taker_execution', 'wait_for_maker_execution'],
                       'failed',
                       after=[omit_args_and_kwargs(fsm.swap.punish_maker),
                              omit_args_and_kwargs(fsm.swap.punish_taker), 'finalize'])

    fsm.add_transition('finalize', ['traded', 'untraded', 'failed', 'uncommitted'], 'processed',
                       after=[fsm.set_terminated_state, omit_args_and_kwargs(fsm.swap.cleanup)])

    # refund transfers that don't trigger any action
    # TODO check if after is right
    fsm.add_transition('transfer_receipt', 'wait_for_taker', '=',
                       unless=[fsm.sender_sent_taker_commitment],
                       after=[fsm.refund_unsuccessful_transfer])
    fsm.add_transition('transfer_receipt', 'wait_for_maker', '=',
                       unless=[fsm.sender_is_maker],
                       after=[fsm.refund_unsuccessful_transfer])
    fsm.add_transition('transfer_receipt',
                       ['wait_for_execution', 'wait_for_taker_execution', 'wait_for_maker_execution',
                         'failed', 'traded', 'uncommitted', 'untraded'],
                        '=',
                       after=[fsm.refund_unsuccessful_transfer])

    if auto_spawn_timeout is True:
        fsm.remove_transition(source='initializing', dest='wait_for_maker', trigger='maker_commitment_msg')
        fsm.add_transition(source='initializing', dest='wait_for_maker', trigger='maker_commitment_msg',
                            after=[fsm.set_maker_commitment, fsm.spawn_timeout])


def event_get_success(event):
    return event.result


def event_get_receipt_kwarg(event):
    receipt = event.kwargs.get('receipt')
    return receipt


def event_get_msg_kwarg(event):
    msg = event.kwargs.get('msg')
    return msg


# FIXME errors
def event_get_msg_or_receipt_kwarg(event):
    msg = event.kwargs.get('msg')
    receipt = event.kwargs.get('receipt')
    if msg and receipt:
        raise ValueError("ambigous arguments, either provide a msg or a receipt")
    if not msg and not receipt:
        raise ValueError("incorrect arguments")
    data = None
    if msg and not receipt:
        data = msg
    if receipt and not msg:
        data = receipt
    if not hasattr(data, 'sender'):
        # TODO better error
        raise AttributeError()
    if data.sender is None:
        raise ValueError()
    return data


# FIXME mocking is not easy when a swap-method is wrapped with this
def omit_args_and_kwargs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        func()
    return wrapper


class SwapStateMachine(Machine):

    def __init__(self, swap, auto_spawn_timeout=True):
        # TODO evaluate if queued_transition is better
        super(SwapStateMachine, self).__init__(self, states=SWAP_BASE_STATES, initial=SWAP_INITIAL_STATE,
                                               send_event=True, ignore_invalid_triggers=True)
        self.taker_commitment_pool = dict()
        self.swap = swap

        self._setup_transitions(auto_spawn_timeout)

    def _setup_transitions(self, auto_spawn_timeout):
        swap_setup_state_transitions(self, auto_spawn_timeout)

    def spawn_timeout(self, event):
        maker_commitment_msg = event_get_msg_kwarg(event)
        seconds_to_timeout = timestamp.seconds_to_timeout(maker_commitment_msg.timeout)
        gevent.spawn_later(seconds_to_timeout, self.swap.trigger_timeout)

    def refund_unsuccessful_transfer(self, event):
        print(event)
        # gets called with every event call, even if it raised an error or the state-transition wasn't successful
        transfer_receipt = event_get_receipt_kwarg(event)
        success = event_get_success(event)

        # refund every receipt that didn't successfully trigger a state change
        if success is False:
            self.swap.queue_refund(transfer_receipt, priority=1, claim_fee=False)

    def set_terminated_state(self, event):
        self.swap.terminated_state = event.transition.source

    def set_taker_execution(self, event):
        swap_execution_msg = event_get_msg_kwarg(event)
        self.swap.taker_swap_execution_msg = swap_execution_msg

    def set_maker_execution(self, event):
        swap_execution_msg = event_get_msg_kwarg(event)
        self.swap.maker_swap_execution_msg = swap_execution_msg

    def set_maker_transfer_receipt(self, event):
        transfer_receipt = event_get_receipt_kwarg(event)
        self.swap.maker_transfer_receipt = transfer_receipt

    def set_taker_transfer_receipt(self, event):
        transfer_receipt = event_get_receipt_kwarg(event)
        self.swap.taker_transfer_receipt = transfer_receipt

    def set_maker_commitment(self, event):
        maker_commitment_msg = event_get_msg_kwarg(event)
        self.swap.maker_commitment_msg = maker_commitment_msg

    def accept_taker_commitment_from_receipt(self, event):
        transfer_receipt = event_get_receipt_kwarg(event)
        taker_commitment = self.taker_commitment_pool[transfer_receipt.sender]
        self.swap.taker_commitment_msg = taker_commitment

    def sender_is_maker(self, event):
        msg_or_receipt = event_get_msg_or_receipt_kwarg(event)
        return self.swap.is_maker(msg_or_receipt.sender)

    def sender_is_taker(self, event):
        msg_or_receipt = event_get_msg_or_receipt_kwarg(event)
        return self.swap.is_taker(msg_or_receipt.sender)

    def sender_sent_taker_commitment(self, event):
        msg_or_receipt = event_get_msg_or_receipt_kwarg(event)
        return msg_or_receipt.sender in self.taker_commitment_pool

    def queue_commitment(self, event):
        commitment_msg = event_get_msg_kwarg(event)
        if commitment_msg.sender not in self.taker_commitment_pool:
            self.taker_commitment_pool[commitment_msg.sender] = commitment_msg
        else:
            # TODO
            # sent another message... what should we allow here? replace, ignore?
            pass
