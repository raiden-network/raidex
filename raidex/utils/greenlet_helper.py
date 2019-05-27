from gevent import spawn_later, kill

from raidex.raidex_node.architecture.state_change import OfferTimeoutStateChange
from raidex.utils.timestamp import seconds_to_timeout
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes


def future_timeout(offer_id, timeout, threshold=0):

    lifetime = seconds_to_timeout(timeout) - threshold
    return spawn_later(lifetime, dispatch_state_changes, OfferTimeoutStateChange(offer_id, timeout))


def kill_greenlet(greenlet):
    kill(greenlet)


class TimeoutHandler:

    def __init__(self):
        self.timeout_greenlets = dict()

    def create_new_timeout(self, offer_id, threshold=0):

        if self._has_greenlet(offer_id) and not self._is_still_alive(offer_id):
            return False

        self.clean_up_timeout(offer_id)
        timeout_greenlet = future_timeout(offer_id.offer_id, offer_id.timeout_date, threshold)
        self.timeout_greenlets[offer_id.offer_id] = timeout_greenlet
        return True

    def _has_greenlet(self, offer_id):
        if offer_id in self.timeout_greenlets:
            return True
        return False

    def _is_still_alive(self, offer_id):

        if offer_id in self.timeout_greenlets and not self.timeout_greenlets[offer_id]:
            return True
        return False

    def clean_up_timeout(self, offer_id):

        if offer_id in self.timeout_greenlets:
            kill_greenlet(self.timeout_greenlets[offer_id])
            del self.timeout_greenlets[offer_id]