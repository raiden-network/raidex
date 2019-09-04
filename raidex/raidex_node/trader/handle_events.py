from raidex.raidex_node.trader.events import *


def handle_event(trader_client, event):

    if isinstance(event, SwapInitEvent):
        handle_swap_init(trader_client, event)
    if isinstance(event, TransferEvent):
        handle_transfer(trader_client, event)
    if isinstance(event, MakeChannelEvent):
        handle_make_channel(trader_client, event)


def handle_swap_init(trader_client, event):
    match = event.match
    trader_client.initiate_exchange(match)


def handle_transfer(trader_client, event: TransferEvent):
    trader_client.transfer_async(token_address=event.token,
                                 target_address=event.target,
                                 amount=event.amount,
                                 identifier=event.identifier)


def handle_make_channel(trader_client, event: MakeChannelEvent):
    trader_client.make_channel(event.partner_address, event.token_address, event.total_deposit)
