from __future__ import print_function

from gevent import monkey

monkey.patch_socket()

import requests
from ethereum.utils import encode_hex

from raidex.raidex_node.offer_book import OfferType
from raidex.utils.gevent_helpers import make_async


class TraderClient(object):
    """Handles the actual token swap. A client/server mock for now. Later will use a raiden node"""

    def __init__(self, address):
        self.address = address
        self.base_amount = 100
        self.counter_amount = 100
        pass

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

        result = requests.post('http://localhost:5001/api/expect', json=body)
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

        result = requests.post('http://localhost:5001/api/exchange', json=body)
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
