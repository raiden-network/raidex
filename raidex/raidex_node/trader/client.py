from __future__ import print_function


import json
from gevent import monkey; monkey.patch_socket()
from gevent import Greenlet
from gevent.queue import Queue
from polling import poll

import requests
from eth_utils import encode_hex
from raidex.raidex_node.trader.events import TraderEvent
from raidex.utils.address import encode_address
from raidex.raidex_node.trader.handle_events import handle_event
from raidex.raidex_node.matching.match import Match
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.order.offer import OfferType
from raidex.trader_mock.trader import (
    Listener,
    EventPaymentReceivedSuccess,
    BalanceUpdateTask
)
from raidex.utils.gevent_helpers import make_async
from raidex.raidex_node.architecture.event_architecture import Processor
import structlog

log = structlog.get_logger('trader client')


class TraderClient(Processor):
    """Handles the actual token swap. A client/server mock for now. Later will use a raiden node"""

    def __init__(self, address, host='localhost', port=5001, market: TokenPair = None, api_version='v1' , commitment_amount=10):
        super(TraderClient, self).__init__(TraderEvent)
        self.address = address
        self.market = market
        self.port = port
        self.api_version = api_version
        self.base_amount = 100
        self.quote_amount = 100
        self.commitment_balance = commitment_amount
        self._is_running = False
        self.apiUrl = 'http://{}:{}/api/{}'.format(host, port, api_version)
        self.events = {}

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        if not self.is_running:
            BalanceUpdateTask(self).start()
            self._is_running = True

    @make_async
    def expect_exchange_async(self, type_, base_amount, quote_amount, target_address, identifier, secret=None, secret_hash=None):
        """Expect a token swap

        Args:
            type_ (OfferType): of the swap related to the market
            base_amount (int): amount of base units to swap
            quote_amount: amount of quote unit to swap
            target_address: (str)
            identifier: The identifier of this token swap

        Returns:
            AsyncResult: bool: indicates if the swap was successful

        """
        if type_ == OfferType.BUY:
            return self.transfer(self.market.checksum_base_address, target_address, base_amount, identifier, secret, secret_hash)
        return self.transfer(self.market.checksum_quote_address, target_address, quote_amount, identifier, secret, secret_hash)


    @make_async
    def exchange_async(self, type_, base_amount, quote_amount, target_address, identifier, secret=None, secret_hash=None):
        """Executes a token swap

           Args:
               type_ (OfferType): of the swap related to the market
               base_amount (int): amount of base units to swap
               quote_amount: amount of quote unit to swap
               target_address: (str)
               identifier: The identifier of this token swap

           Returns:
               AsyncResult: bool: indicates if the swap was successful

           """

#        body = {'type': type_.value, 'baseAmount': base_amount, 'quoteAmount': quote_amount,
#                'selfAddress': encode_address(self.address), 'targetAddress': encode_address(target_address),
#                'identifier': identifier}
#
#        result = requests.post('{}/exchange'.format(self.apiUrl), json=body)
#        success = result.json()['data']
#        if success:
#            self._execute_exchange(type_, base_amount, quote_amount)
#        return success
        if type_ == OfferType.BUY:
            return self.transfer(self.market.checksum_quote_address, target_address, quote_amount, identifier, secret, secret_hash)
        return self.transfer(self.market.checksum_base_address, target_address, base_amount, identifier, secret, secret_hash)

    @make_async
    def initiate_exchange(self, match: Match):
        target = match.target
        amount = match.get_send_amount()
        identifier = match.offer.offer_id
        token = match.get_token_from_market(self.market)
        secret = match.get_secret()
        secret_hash = match.get_secret_hash()

        return self.transfer(token, target, amount, identifier, secret, secret_hash)


    @make_async
    def transfer_async(self, token_address, target_address, amount, identifier):
        return self.transfer(token_address, target_address, amount, identifier)

    def transfer(self, token_address, target_address, amount, identifier, secret=None, secret_hash=None):
        """Makes a transfer, used for the commitments

           Args:
               amount (int): amount of base units to swap
               token_address: address of token contract
               target_address: address of the recipient of the transfer
               identifier: The identifier of this transfer, should match the offer_id

           Returns:
               AsyncResult: bool: indicates if the transfer was successful

           """

        encoded_token = encode_address(token_address)
        encoded_target = encode_address(target_address)

        body = {'amount': int(amount), 'identifier': identifier}

        if secret is not None:
            body['secret'] = encode_hex(secret)
            log.debug(f'Secret given: {body["secret"]}')
        if secret is not None:
            body['secret_hash'] = encode_hex(secret_hash)
            log.debug(f'Secret Hash given: {body["secret_hash"]}')

        result = requests.post('{}/payments/{}/{}'.format(self.apiUrl, encoded_token, encoded_target), json=body)

        log.debug(f'TOKEN: {encoded_token}, ADDRESS: {encoded_target}, AMOUNT: {amount}, IDENTIFIER: {identifier}')

        if result.status_code == 200:
            self.commitment_balance -= amount
        return result

    def listen_for_events(self, transform=None):
        """Starts listening for new messages on this topic

        Args:
            transform : A function that filters and transforms the message
                        should return None if not interested in the message, message will not be returned,
                        otherwise should return the message in a format as needed

        Returns:
            Listener: an object gathering all settings of this listener

        """
        event_queue_async = Queue()

        listener = Listener(self.address, event_queue_async, transform)

        events = {}

        def request_events(events):

            r = requests.get('{}/payments'.format(self.apiUrl))

            for line in r.iter_lines():
                # filter out keep-alive new lines
                if line:
                    decoded_line = line.decode('utf-8')
                    raw_data = json.loads(decoded_line)

                    for e in raw_data:
                        event = encode(e, e['event'])
                        if event is None:
                            continue

                        event_id = event.identifier_tuple

                        if event_id in events:
                            continue

                        transformed_event = transform(event)
                        events[event_id] = transformed_event

                        if transformed_event is not None:
                            event_queue_async.put(transformed_event)

        Greenlet.spawn(poll, target=request_events, args=(events,), step=2, poll_forever=True)

        return listener

    def stop_listen(self):
        # provide same interface as Trader, as defined/used in the EventListener
        # TODO do we need to close the request here?
        pass


def encode(event, type_):
    if type_ == 'EventPaymentReceivedSuccess':
        return EventPaymentReceivedSuccess(event['initiator'], event['amount'], event['identifier'])
    #raise Exception('encoding error: unknown-event-type')
    return None

