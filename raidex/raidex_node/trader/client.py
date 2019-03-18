from __future__ import print_function


import json
from gevent import monkey; monkey.patch_socket()
from gevent import Greenlet
from gevent.queue import Queue
from polling import poll

import requests
from eth_utils import encode_hex

from raidex.utils.address import encode_address, binary_address

from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.trader.trader import (
    Listener,
    EventPaymentReceivedSuccess,
    BalanceUpdateTask
)
from raidex.utils.gevent_helpers import make_async
import structlog

log = structlog.get_logger('trader client')


class TraderClient(object):
    """Handles the actual token swap. A client/server mock for now. Later will use a raiden node"""

    def __init__(self, address, host='localhost', port=5001, api_version='v1' , commitment_amount=10):
        self.address = address
        self.port = port
        self.api_version = api_version
        self.base_amount = 100
        self.counter_amount = 100
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
    def expect_exchange_async(self, base_address, base_amount, counter_amount, target_address, identifier):
        """Expect a token swap

        Args:
            type_ (OfferType): of the swap related to the market
            base_amount (int): amount of base units to swap
            counter_amount: amount of counter unit to swap
            target_address: (str)
            identifier: The identifier of this token swap

        Returns:
            AsyncResult: bool: indicates if the swap was successful

        """
#        body = {'type': type_.value, 'baseAmount': base_amounself, self_address, target_address, amount, identifiert, 'counterAmount': counter_amount,
#                'selfAddress': encode_hex(self.address), 'targetAddress': encode_hex(target_address),
#                'identifier': identifier}
#
#        result = requests.post('{}/expect'.format(self.apiUrl), json=body)
#        success = result.json()['data']
#        if success:
#            self._execute_exchange(OfferType.opposite(type_), base_amount, counter_amount)
#        return success

        self.transfer()


    @make_async
    def exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):
        """Executes a token swap

           Args:
               type_ (OfferType): of the swap related to the market
               base_amount (int): amount of base units to swap
               counter_amount: amount of counter unit to swap
               target_address: (str)
               identifier: The identifier of this token swap

           Returns:
               AsyncResult: bool: indicates if the swap was successful

           """

        body = {'type': type_.value, 'baseAmount': base_amount, 'counterAmount': counter_amount,
                'selfAddress': encode_address(self.address), 'targetAddress': encode_address(target_address),
                'identifier': identifier}

        result = requests.post('{}/exchange'.format(self.apiUrl), json=body)
        success = result.json()['data']
        if success:
            self._execute_exchange(type_, base_amount, counter_amount)
        return success

    def _execute_exchange(self, type_, base_amount, counter_amount):
        if type_ is OfferType.SELL:
            self.base_amount -= base_amount
            self.counter_amount += counter_amount
        elif type_ is OfferType.BUY:
            self.base_amount += base_amount
            self.counter_amount -= counter_amount
        else:
            raise ValueError('Unknown OfferType')

    @make_async
    def transfer_async(self, token_address, target_address, amount, identifier):
        return self.transfer(token_address, target_address, amount, identifier)

    def transfer(self, token_address, target_address, amount, identifier):
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

        body = {'amount': amount, 'identifier': identifier}
        result = requests.post('{}/payments/{}/{}'.format(self.apiUrl, encoded_token, encoded_target), json=body)

        # print("ADDRESS: {}, AMOUNT: {}, IDENTIFIER: {}".format(target_address, amount, identifier))

        success = result.json()
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
                        if 'identifier' in e and e['identifier'] not in events:
                            event = encode(e, e['event'])

                            if transform is not None and event is not None:
                                event = transform(event)
                                events[e['identifier']] = event
                            if event is not None:
                                event_queue_async.put(event)
                                print(event)
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


