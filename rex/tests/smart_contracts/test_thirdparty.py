# -*- coding: utf8 -*-
import pytest

from rex.utils.smart_contracts import get_contract_path
from ethereum import tester
from ethereum.tester import ABIContract, ContractTranslator, TransactionFailed


@pytest.mark.skip(reason='Third party smart contract deprecated')
def test_thirdparty():
    third_party_path = get_contract_path('ThirdParty.sol')

    state = tester.state()
    third_party = state.abi_contract(
        None,
        path=third_party_path,
        language='solidity',
        constructor_parameters=[tester.a0],
    )

    assert third_party.thirdParty() == tester.a0.encode('hex')
