from datetime import datetime, timedelta
# TODO test the timestamp and roundings


def _dt_to_ms_timestamp(dt, epoch=datetime(1970, 1, 1)):
    td = dt - epoch
    return int(round(td.total_seconds() * 1000.0))


def _ms_timestamp_to_dt(timestamp, epoch=datetime(1970, 1, 1)):
    return epoch + timedelta(milliseconds=timestamp)


def to_str_repr(timestamp : int):
    return _ms_timestamp_to_dt(timestamp).strftime("%H:%M:%S")


def to_seconds(ms):
    return ms / 1000.


def to_milliseconds(s):
    return s * 1000.


def time_plus(seconds=0, milliseconds=0, microseconds=0):
    td = timedelta(seconds=seconds, milliseconds=milliseconds, microseconds=microseconds)
    return _dt_to_ms_timestamp(datetime.utcnow() + td)


def time_minus(seconds=0, milliseconds=0, microseconds=0):
    td = timedelta(seconds=seconds, milliseconds=milliseconds, microseconds=microseconds)
    return _dt_to_ms_timestamp(datetime.utcnow() - td)


def time():
    now = datetime.utcnow()
    return _dt_to_ms_timestamp(now)


def time_int():
    return time()


def seconds_to_timeout(timeout):
    timeout_dt = _ms_timestamp_to_dt(timeout)
    dt = timeout_dt - datetime.utcnow()
    return dt.total_seconds()


def timed_out(timeout):
    timeout_dt = _ms_timestamp_to_dt(timeout)
    return timeout_dt < datetime.utcnow()



