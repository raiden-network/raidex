
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.architecture.state_change import NewLimitOrderStateChange, CancelLimitOrderStateChange
from raidex.utils.random import create_random_32_bytes_id
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes


def on_api_call(raidex_node: RaidexNode, data):

    event_name = data['event']
    print(event_name)
    if event_name == 'NewLimitOrder':
        return handle_new_limit_order(data)
    if event_name == 'CancelLimitOrder':
        return handle_cancel_limit_order(raidex_node, data)


def handle_new_limit_order(data):

    data['order_id'] = create_random_32_bytes_id()
    state_change = NewLimitOrderStateChange(data)
    dispatch_state_changes(state_change)

    return data['order_id']


def handle_cancel_limit_order(raidex_node: RaidexNode, data):
    order_id = data['order_id']

    if order_id not in raidex_node.data_manager.orders:
        raise Exception

    if raidex_node.data_manager.orders[order_id].open:
        state_change = CancelLimitOrderStateChange(data)
        dispatch_state_changes(state_change)
        return data['order_id']

    raise Exception
