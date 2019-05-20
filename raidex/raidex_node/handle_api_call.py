from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.architecture.state_change import NewLimitOrderStateChange
from raidex.utils.random import create_random_32_bytes_id
from raidex.raidex_node.architecture.event_architecture import dispatch_state_change


def on_api_call(raidex_node: RaidexNode, data):

    event_name = data['event']

    if event_name == 'NewLimitOrder':
        return handle_new_limit_order(raidex_node, data)


def handle_new_limit_order(raidex_node: RaidexNode, data):

    data['order_id'] = create_random_32_bytes_id()
    state_change = NewLimitOrderStateChange(data)
    dispatch_state_change(state_change)

    return data['order_id']

