import gevent
from raidex.utils import timestamp, pex
import structlog
from ethereum.utils import encode_hex
from raidex.message_broker.listeners import TakerListener, listener_context
from raidex.utils.gevent_helpers import switch_context

log = slogging.get_logger('node.exchange')


class MakerExchangeTask(gevent.Greenlet):
    """
    Spawns and manages one offer & handles/initiates the respective commitment,
    when a taker is found, it executes the token swap and reports the execution

    """

    def __init__(self, offer, maker_address, commitment_service, message_broker, trader):
        self.offer = offer
        self.maker_address = maker_address
        self.commitment_service = commitment_service
        self.message_broker = message_broker
        self.trader = trader
        gevent.Greenlet.__init__(self)
        
    def _run(self):
        seconds_to_timeout = timestamp.seconds_to_timeout(self.offer.timeout)
        if seconds_to_timeout <= 0:
            return False
        timeout = gevent.Timeout(seconds_to_timeout)
        timeout.start()
        try:
            proven_offer = self.commitment_service.maker_commit_async(self.offer).get()
            if proven_offer is None:
                log.debug('No proven offer received for {}'.format(pex(self.offer.offer_id)))
                return False
            log.debug('Wait for taker of {}'.format(pex(self.offer.offer_id)))
            with listener_context(TakerListener(self.offer, self.message_broker, self.maker_address)) as taker_listener:
                log.debug('Broadcast proven_offer for {}'.format(pex(self.offer.offer_id)))
                self.message_broker.broadcast(proven_offer)
                taker_address = taker_listener.get()
                log.debug('taker address: {}'.format(encode_hex(taker_address)))

                log.debug('Found taker, execute swap of {}'.format(pex(self.offer.offer_id)))
                status = self.trader.exchange_async(self.offer.type, self.offer.base_amount, self.offer.counter_amount,
                                                    taker_address, self.offer.offer_id).get()
                if status:
                    log.debug('Swap of {} done'.format(pex(self.offer.offer_id)))
                    self.commitment_service.report_swap_executed(self.offer.offer_id)
                    #  TODO check refund minus fee
                else:
                    log.debug('Swap of {} failed'.format(pex(self.offer.offer_id)))
                    #  TODO check refund
                return status
        except gevent.Timeout as t:
            if t is not timeout:
                raise  # not my timeout
            return False
        finally:
            timeout.cancel()

    @property
    def amount(self):
        return self.offer.amount


class TakerExchangeTask(gevent.Greenlet):
    """
    Tries to take a specific offer:
        it will first try to initiate a commitment at the `offer.commitment_service`
        when successful, it will initiate /coordinate the assetswap with the maker
    """

    def __init__(self, offer, commitment_service, message_broker, trader):
        self.offer = offer
        self.commitment_service = commitment_service
        self.message_broker = message_broker
        self.trader = trader
        gevent.Greenlet.__init__(self)

    def _run(self):
        seconds_to_timeout = timestamp.seconds_to_timeout(self.offer.timeout)
        if seconds_to_timeout <= 0:
            return False
        timeout = gevent.Timeout(seconds_to_timeout)
        timeout.start()
        try:
            proven_commitment = self.commitment_service.taker_commit_async(self.offer).get()
            if proven_commitment is None:
                log.debug('No proven commitment received for {}'.format(pex(self.offer.offer_id)))
                return False
            status_async = self.trader.expect_exchange_async(self.offer.type, self.offer.base_amount,
                                                             self.offer.counter_amount, self.offer.maker_address,
                                                             self.offer.offer_id)
            switch_context()  # give async function chance to execute
            log.debug('Send proven-commitment of {} to maker'.format(pex(self.offer.offer_id)))
            self.message_broker.send(self.offer.maker_address, proven_commitment)
            status = status_async.get()
            if status:
                log.debug('Swap of {} done'.format(pex(self.offer.offer_id)))
                self.commitment_service.report_swap_executed(self.offer.offer_id)
            else:
                log.debug('Swap of {} failed'.format(pex(self.offer.offer_id)))
                # TODO check refund
            return status
        except gevent.Timeout as t:
            if t is not timeout:
                raise  # not my timeout
            return False
        finally:
            timeout.cancel()

    @property
    def amount(self):
        return self.offer.amount
