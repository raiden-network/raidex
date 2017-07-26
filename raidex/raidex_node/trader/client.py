from __future__ import print_function

import json
from gevent import monkey; monkey.patch_socket()
from gevent import Greenlet
from gevent.queue import Queue


import requests
from ethereum.utils import encode_hex, decode_hex

from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.trader.trader import (
    Listener,
    TransferReceivedEvent,
    BalanceUpdateTask
)
from raidex.utils.gevent_helpers import make_async


class TraderClient(object):
    """Handles the actual token swap. A client/server mock for now. Later will use a raiden node"""

    def __init__(self, address, host='localhost', port=5001, commitment_amount=10):
        self.address = address
        self.port = port
        self.base_amount = 100
        self.counter_amount = 100
        self.commitment_balance = commitment_amount
        self._is_running = False
        self.apiUrl = 'http://{}:{}/api'.format(host, port)

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        if not self.is_running:
            BalanceUpdateTask(self).start()
            self._is_running = True

    @make_async
    def expect_exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):
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
        body = {'type': type_.value, 'baseAmount': base_amount, 'counterAmount': counter_amount,
                'selfAddress': encode_hex(self.address), 'targetAddress': encode_hex(target_address),
                'identifier': identifier}

        result = requests.post('{}/expect'.format(self.apiUrl), json=body)
        success = result.json()['data']
        if success:
            self._execute_exchange(OfferType.opposite(type_), base_amount, counter_amount)
        return success

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
                'selfAddress': encode_hex(self.address), 'targetAddress': encode_hex(target_address),
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
    def transfer_async(self, target_address, amount, identifier):
        return self.transfer(target_address, amount, identifier)

    def transfer(self, target_address, amount, identifier):
        """Makes a transfer, used for the commitments

           Args:
               amount (int): amount of base units to swap
               target_address: (str) address of the recipient of the transfer
               identifier: The identifier of this transfer, should match the offer_id

           Returns:
               AsyncResult: bool: indicates if the transfer was successful

           """

        body = {'amount': amount, 'selfAddress': encode_hex(self.address), 'targetAddress': encode_hex(target_address),
                'identifier': identifier}

        result = requests.post('{}/transfer'.format(self.apiUrl), json=body)
        # FIXME data field not available on some errors..
        success = result.json()['data']
        if success is True:
            self.commitment_balance -= amount
        return success

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

        def run():
            r = requests.get('{}/events/{}'.format(self.apiUrl, encode_hex(self.address)), stream=True)
            for line in r.iter_lines():
                # filter out keep-alive new lines
                if line:
                    decoded_line = line.decode('utf-8')
                    raw_data = json.loads(decoded_line)['data']
                    event = encode(raw_data['event'], raw_data['type'])
                    if transform is not None:
                        event = transform(event)
                    if event is not None:
                        event_queue_async.put(event)

        Greenlet.spawn(run)

        return listener

    def stop_listen(self):
        # provide same interface as Trader, as defined/used in the EventListener
        # TODO do we need to close the request here?
        pass


def encode(event, type_):
    if type_ == 'TransferReceivedEvent':
        return TransferReceivedEvent(decode_hex(event['sender']), event['amount'], event['identifier'])
    raise Exception('encoding error: unknown-event-type')
