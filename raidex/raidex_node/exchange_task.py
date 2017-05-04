import gevent
from raidex.utils import timestamp
from ethereum import slogging
from ethereum.utils import encode_hex
from raidex.message_broker.listeners import TakerListener
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
            proof = self.commitment_service.maker_commit_async(self.offer).get()
            log.debug('Broadcast proof for {}'.format(self.offer.offer_id))
            self.message_broker.broadcast(proof)
            log.debug('Wait for taker of {}..'.format(self.offer.offer_id))
            # TODO verify proof
            taker_address = TakerListener(self.offer, self.message_broker, encode_hex(self.maker_address)).get_once()
            log.debug('Found taker, execute swap of {}'.format(self.offer.offer_id))
            status = self.trader.exchange_async(self.offer.type_, self.offer.base_amount, self.offer.counter_amount,
                                                taker_address, self.offer.offer_id).get()
            if status:
                log.debug('Swap of {} done'.format(self.offer.offer_id))
                self.commitment_service.swap_executed(self.offer.offer_id)
                #  TODO check refund minus fee
            else:
                log.debug('Swap of {} failed'.format(self.offer.offer_id))
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
            proof = self.commitment_service.taker_commit_async(self.offer).get()
            status_async = self.trader.expect_exchange_async(self.offer.type_, self.offer.base_amount,
                                                             self.offer.counter_amount, self.offer.maker_address,
                                                             self.offer.offer_id)
            switch_context()  # give async function chance to execute
            # FIXME hack for now, later cs should send this:
            self.message_broker.broadcast(self.commitment_service.create_taken(self.offer.offer_id))
            log.debug('Send proof of {} to maker'.format(self.offer.offer_id))
            self.message_broker.send(encode_hex(self.offer.maker_address), proof)
            status = status_async.get()
            if status:
                log.debug('Swap of {} done'.format(self.offer.offer_id))
                self.commitment_service.swap_executed(self.offer.offer_id)
            else:
                log.debug('Swap of {} failed'.format(self.offer.offer_id))
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
