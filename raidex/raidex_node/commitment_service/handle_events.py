from gevent import spawn

from raidex.raidex_node.commitment_service.events import *
from raidex.message_broker.listeners import TakerListener, listener_context


def handle_event(self, event):
    if isinstance(event, CommitEvent):
        if event.offer.is_maker():
            self.maker_commit(event.offer)
        else:
            self.taker_commit(event.offer)
    if isinstance(event, CommitmentProvedEvent):
        spawn(wait_for_taker, event, self.message_broker, self.state_change_q)


def wait_for_taker(event, message_broker, state_change_q):
    with listener_context(TakerListener(event.offer, message_broker)) as taker_listener:
        taker_address = taker_listener.get()
        print(f'TAKER_ADDRESS: {taker_address}')
        state_change_q.put(taker_address)