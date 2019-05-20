import gevent

import structlog
from raidex import messages
from raidex.utils import pex

from raidex.commitment_service.swap import SwapFactory
from raidex.raidex_node.listener_tasks import ListenerTask
from raidex.trader_mock.trader import TransferReceipt
from raidex.trader_mock.trader import TransferReceivedListener
from raidex.message_broker.listeners import TakerCommitmentListener, MakerCommitmentListener, SwapExecutionListener

log = structlog.get_logger('commitment_service')
log_swaps = structlog.get_logger('commitment_service.asset_swaps')
log_messaging = structlog.get_logger('commitment_service.messaging')
log_refunds = structlog.get_logger('commitment_service.refunds')
log_trader = structlog.get_logger('commitment_service.trader')


class QueueListenerTask(gevent.Greenlet):
    def __init__(self, queue):
        self.queue = queue
        gevent.Greenlet.__init__(self)

    def _run(self):
        while True:
            data = self.queue.get()
            self.process(data)

    def process(self, data):
        raise NotImplementedError


class RefundTask(QueueListenerTask):
    def __init__(self, trader_client, refund_queue, commitment_token_address, fee_rate=None):
        self.refund_queue = refund_queue
        self.trader_client = trader_client
        self.commitment_token_address = commitment_token_address
        self.fee_rate = fee_rate
        super(RefundTask, self).__init__(refund_queue)

    def process(self, data):
        refund = data
        amount = refund.receipt.amount
        if self.fee_rate is not None and refund.claim_fee is True:
            amount -= amount * self.fee_rate
        transfer_async_result = self.trader_client.transfer_async(self.commitment_token_address,
                                                                  refund.receipt.initiator,
                                                                  amount,
                                                                  refund.receipt.identifier)

        def get_and_requeue(async_result, refund_, queue):
            # FIXME this could block a greenlet forever, leaving the refund in nirvana
            success = async_result.get()

            if success.status_code == 200:
                log_trader.debug('Refund successful {}'.format(refund_))
            else:
                queue.put(refund_)
                log_trader.debug('Refunding failed for {}, retrying'.format(refund_))

        # spawn so that we can process the next refunds in the queue
        # gevent.spawn(get_and_requeue, transfer_async_result, refund, self.refund_queue)
        get_and_requeue(transfer_async_result, refund, self.refund_queue)


class MessageSenderTask(QueueListenerTask):

    def __init__(self, message_broker, message_queue, sign_func):
        self.message_broker = message_broker
        self._sign_func = sign_func
        super(MessageSenderTask, self).__init__(message_queue)

    def process(self, data):
        msg, recipient = data
        self._sign_func(msg)
        # FIXME make async
        # recipient == None is indicating a broadcast
        if recipient is None:
            success = self.message_broker.broadcast(msg)
            if success is True:
                log_messaging.debug('Broadcast successful: {}'.format(msg))
        else:

            success = self.message_broker.send(topic=recipient, message=msg)
            if success is True:
                log_messaging.debug('Sending successful: {} // recipient={}'.format(msg, pex(recipient)))


class TransferReceivedTask(ListenerTask):

    def __init__(self, swaps, trader_client):
        self.swaps = swaps
        super(TransferReceivedTask, self).__init__(TransferReceivedListener(trader_client))

    def process(self, data):
        transfer_receipt = data
        if not hasattr(transfer_receipt, 'identifier'):
            raise ValueError()
        if not isinstance(transfer_receipt, TransferReceipt):
            raise ValueError()

        offer_id = transfer_receipt.identifier
        swap = self.swaps.get(offer_id)

        log_trader.debug(str(transfer_receipt))

        if swap is not None:
            swap.hand_transfer_receipt(transfer_receipt)
        else:
            #TODO
            # refund
            pass


class TakerCommitmentTask(ListenerTask):

    def __init__(self, swaps, message_broker, self_address):
        self.swaps = swaps
        super(TakerCommitmentTask, self).__init__(TakerCommitmentListener(message_broker, topic=self_address))

    def process(self, data):
        taker_commitment_msg = data
        if not hasattr(taker_commitment_msg, 'offer_id'):
            raise ValueError()
        if not isinstance(taker_commitment_msg, messages.TakerCommitment):
            raise ValueError()
        offer_id = taker_commitment_msg.offer_id
        swap = self.swaps.get(offer_id)

        if swap is not None:
            swap.hand_taker_commitment_msg(taker_commitment_msg)


class MakerCommitmentTask(ListenerTask):

    def __init__(self, swaps, refund_queue, message_queue, message_broker, self_address):
        self.factory = SwapFactory(swaps, refund_queue, message_queue)
        super(MakerCommitmentTask, self).__init__(MakerCommitmentListener(message_broker, topic=self_address))

    def process(self, data):
        maker_commitment_msg = data
        if not hasattr(maker_commitment_msg, 'offer_id'):
            raise ValueError()
        if not isinstance(maker_commitment_msg, messages.MakerCommitment):
            raise ValueError()

        offer_id = maker_commitment_msg.offer_id

        swap = self.factory.make_swap(offer_id)

        log_messaging.debug(str(maker_commitment_msg))
        log_messaging.debug("Offer ID: {}".format(offer_id))

        if swap is not None:
            swap.hand_maker_commitment_msg(maker_commitment_msg)



class SwapExecutionTask(ListenerTask):

    def __init__(self, swaps, message_broker, self_address):
        self.swaps = swaps
        super(SwapExecutionTask, self).__init__(SwapExecutionListener(message_broker, topic=self_address))

    def process(self, data):
        swap_execution_msg = data
        if not hasattr(swap_execution_msg, 'offer_id'):
            raise ValueError()
        if not isinstance(swap_execution_msg, messages.SwapExecution):
            raise ValueError()

        offer_id = swap_execution_msg.offer_id
        swap = self.swaps.get(offer_id)
        if swap is not None:
            swap.hand_swap_execution_msg(swap_execution_msg)
