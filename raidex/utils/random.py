from uuid import uuid4


def create_random_32_bytes_id():
    return int(uuid4().int % (2 ** 32 - 1))