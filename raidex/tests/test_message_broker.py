import pytest

from raidex.message_broker.message_broker import MessageBroker


@pytest.fixture()
def message_broker():
    return MessageBroker()


def test_send(message_broker):
    listener = message_broker.listen_on('test1')
    message_broker.send('test1', 'testmessage')
    message = listener.message_queue_async.get()
    assert message == 'testmessage', 'Did not receive the right message'


def test_listen(message_broker):

    listener = message_broker.listen_on('test2')
    message_broker.send('test1', 'testmessage')
    is_empty = listener.message_queue_async.empty()
    assert is_empty, 'Did receive a message it should not'


def test_broadcast(message_broker):
    listeners = []
    for i in range(10):
        listeners.append(message_broker.listen_on_broadcast())
    message_broker.broadcast('testmessage')
    number_of_messages = 0
    for listener in listeners:
        number_of_messages += listener.message_queue_async.qsize()
    assert number_of_messages == 10, 'Did not broadcast to all listeners'


def test_stop_listen(message_broker):

    listener = message_broker.listen_on('test1')
    message_broker.stop_listen(listener)
    message_broker.send('test1', 'testmessage')
    assert listener.message_queue_async.empty(), 'Did receive a message it should not'
