import time as ptime


def to_seconds(ms):
    """Return representation in pythons `time.time()` scale.
    """
    return ms / 1000.


def time():
    now = ptime.time()
    return int(round(now * 1000))


def time_int():
    return time()


def time_plus(seconds):
    now = ptime.time()
    return int(round((now + seconds) * 1000))


def seconds_to_timeout(timeout):
    return timeout / 1000 - ptime.time()
