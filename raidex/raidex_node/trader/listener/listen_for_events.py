import json
import requests
from gevent import Greenlet
from polling import poll
from raidex.raidex_node.trader.listener.events import PaymentReceivedEvent, ChannelStatusRaidenEvent
from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.utils.address import binary_address
from raidex.constants import RAIDEN_POLL_INTERVAL


def raiden_poll(trader, interval=RAIDEN_POLL_INTERVAL, endpoint='payments'):

    raiden_events = {}

    def request_events(events):

        r = requests.get(f'{trader.apiUrl}/{endpoint}')

        for line in r.iter_lines():
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode('utf-8')
                raw_data = json.loads(decoded_line)

                for e in raw_data:
                    event = encode(e, e['event'])
                    if event is None:
                        continue

                    event_id = event.identifier_tuple

                    if event_id in events:
                        continue

                    events[event_id] = event

                    dispatch_events([event])

    listener_greenlet = Greenlet(poll, target=request_events, args=(raiden_events,), step=interval, poll_forever=True)

    return listener_greenlet


def encode(event, type_):
    if type_ == 'EventPaymentReceivedSuccess':
        return PaymentReceivedEvent(binary_address(event['initiator']), event['amount'], event['identifier'])
    # raise Exception('encoding error: unknown-event-type')
    return None


def raiden_poll_channel(trader, interval=10):

    raiden_events = {}

    def request_events(events):

        r = requests.get(f'{trader.apiUrl}/channels')

        for line in r.iter_lines():
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode('utf-8')
                raw_data = json.loads(decoded_line)
                event = ChannelStatusRaidenEvent(raw_data)
                dispatch_events([event])

    listener_greenlet = Greenlet(poll, target=request_events, args=(raiden_events,), step=interval, poll_forever=True)

    return listener_greenlet
