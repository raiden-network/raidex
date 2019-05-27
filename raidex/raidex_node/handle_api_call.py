
from raidex.raidex_node.architecture.state_change import NewLimitOrderStateChange
from raidex.utils.random import create_random_32_bytes_id
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes


def on_api_call(data):

    event_name = data['event']

    if event_name == 'NewLimitOrder':
        return handle_new_limit_order(data)


def handle_new_limit_order(data):

    data['order_id'] = create_random_32_bytes_id()
    state_change = NewLimitOrderStateChange(data)
    dispatch_state_changes(state_change)

    return data['order_id']

