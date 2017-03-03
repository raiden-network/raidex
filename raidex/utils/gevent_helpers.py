from functools import wraps

import gevent
from gevent.event import AsyncResult
from gevent.queue import Queue


def make_async(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        result_async = AsyncResult()
        gevent.spawn(func, *args, **kwargs).link(result_async)
        return result_async

    return wrapper


def make_stream(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        queue = Queue()

        def run():
            for element in func(*args, **kwargs):
                queue.put(element)

        gevent.spawn(run)

    return wrapper


def switch_context():
    gevent.sleep(0.001)