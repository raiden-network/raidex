from eth_utils import (
    to_checksum_address,
    is_checksum_address,
    is_hex_address,
    is_binary_address,
    decode_hex)


def encode_address(address_bytes):
    return to_checksum_address(address_bytes)


def binary_address(address_repr):

    if is_binary_address(address_repr):
        return address_repr
    if is_checksum_address(address_repr):
        return decode_hex(address_repr)

    raise TypeError(
        "decode_address requires address representation either in 0x prefixed String or valid bytes format \
         as argument. Got: {0}".format(repr(address_repr))
    )


def encode_topic(topic):

    try:
        if isinstance(topic, bytes) or is_hex_address(topic):
            return to_checksum_address(topic)
        if isinstance(topic, str) or is_checksum_address(topic):
            return topic
        raise TypeError
    except:
        raise TypeError(
            "encode_topic requires address representation either in 0x prefixed String or valid bytes format \
             as argument. Got: {0}".format(repr(topic))
        )


def decode_topic(topic):

    if is_checksum_address(topic):
        return decode_hex(topic)
    return topic


