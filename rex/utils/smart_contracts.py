import os

import rex


def get_contract_path(contract_name):
    project_directory = os.path.dirname(rex.__file__)
    contract_path = os.path.join(project_directory, 'smart_contracts', contract_name)
    return os.path.realpath(contract_path)
