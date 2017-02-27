import os
import time

import raidex


def get_contract_path(contract_name):
    project_directory = os.path.dirname(raidex.__file__)
    contract_path = os.path.join(project_directory, 'smart_contracts', contract_name)
    return os.path.realpath(contract_path)
