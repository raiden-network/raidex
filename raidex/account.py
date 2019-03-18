import json

from typing import Dict

from eth_utils import remove_0x_prefix, decode_hex, encode_hex
from eth_keyfile import decode_keyfile_json
from eth_keys import keys


class Account:
    """Represents an account.  """

    def __init__(self, keystore, path, password: str = None):
        """
        Args:
            keystore: the key store as a dictionary (as decoded from json)
            password: The password used to unlock the keystore
            path: absolute path to the associated keystore file (`None` for in-memory accounts)
        """

        self.keystore = keystore
        self.locked = True
        self.path = path
        self._privkey: keys.PrivateKey = None
        self._address = None

        try:
            self._address = decode_hex(self.keystore['address'])

        except KeyError:
            pass

        if password is not None:
            self.unlock(password)

    @classmethod
    def load(cls, path: str = None, file=None, password: str = None) -> 'Account':
        """Load an account from a keystore file.

        Args:
            path: full path to the keyfile
            file: already loaded file
            password: the password to decrypt the key file or `None` to leave it encrypted
        """
        if file is None:
            file = open(path, 'r')

        keystore = json.load(file)

        if not check_keystore_json(keystore):
            raise ValueError('Invalid keystore file')
        return Account(keystore, path, password)

    def dump(self, include_address=True, include_id=True) -> str:
        """Dump the keystore for later disk storage.

        The result inherits the entries `'crypto'` and `'version`' from `account.keystore`, and
        adds `'address'` and `'id'` in accordance with the parameters `'include_address'` and
        `'include_id`'.

        If address or id are not known, they are not added, even if requested.

        Args:
            include_address: flag denoting if the address should be included or not
            include_id: flag denoting if the id should be included or not
        """
        d = {
            'crypto': self.keystore['crypto'],
            'version': self.keystore['version'],
        }
        if include_address and self.address is not None:
            d['address'] = remove_0x_prefix(encode_hex(self.address))
        if include_id and self.uuid is not None:
            d['id'] = self.uuid
        return json.dumps(d)

    def unlock(self, password: str):
        """Unlock the account with a password.

        If the account is already unlocked, nothing happens, even if the password is wrong.

        Raises:
            ValueError: (originating in ethereum.keys) if the password is wrong
            (and the account is locked)
        """
        if self.locked:
            self._privkey = decode_keyfile_json(self.keystore, password.encode('UTF-8'))
            self.locked = False
            self.address  # get address such that it stays accessible after a subsequent lock

    def lock(self):
        """Relock an unlocked account.

        This method sets `account.privkey` to `None` (unlike `account.address` which is preserved).
        After calling this method, both `account.privkey` and `account.pubkey` are `None.
        `account.address` stays unchanged, even if it has been derived from the private key.
        """
        self._privkey = None
        self.locked = True

    @property
    def privkey(self):
        """The account's private key or `None` if the account is locked"""
        if not self.locked:
            return self._privkey
        return None

    @property
    def pubkey(self):
        """The account's public key or `None` if the account is locked"""
        if not self.locked:
            return self.privkey.public_key

        return None

    @property
    def address(self):
        """The account's address or `None` if the address is not stored in the key file and cannot
        be reconstructed (because the account is locked)
        """
        if self._address:
            pass
        elif 'address' in self.keystore:
            self._address = decode_hex(self.keystore['address'])
        elif not self.locked:
            self._address = self.privkey.public_key.to_address()
        else:
            return None
        return self._address

    @property
    def canonical_address(self):
        return self.privkey.public_key.to_canonical_address()

    @property
    def uuid(self):
        """An optional unique identifier, formatted according to UUID version 4, or `None` if the
        account does not have an id
        """
        try:
            return self.keystore['id']
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        """Set the UUID. Set it to `None` in order to remove it."""
        if value is not None:
            self.keystore['id'] = value
        elif 'id' in self.keystore:
            self.keystore.pop('id')

    def __repr__(self):
        if self.address is not None:
            address = encode_hex(self.address)
        else:
            address = '?'
        return '<Account(address={address}, id={id})>'.format(address=address, id=self.uuid)


def check_keystore_json(jsondata: Dict) -> bool:
    """ Check if ``jsondata`` has the structure of a keystore file version 3.

    Note that this test is not complete, e.g. it doesn't check key derivation or cipher parameters.
    Copied from https://github.com/vbuterin/pybitcointools

    Args:
        jsondata: Dictionary containing the data from the json file

    Returns:
        `True` if the data appears to be valid, otherwise `False`
    """
    if 'crypto' not in jsondata and 'Crypto' not in jsondata:
        return False
    if 'version' not in jsondata:
        return False
    if jsondata['version'] != 3:
        return False

    crypto = jsondata.get('crypto', jsondata.get('Crypto'))
    if 'cipher' not in crypto:
        return False
    if 'ciphertext' not in crypto:
        return False
    if 'kdf' not in crypto:
        return False
    if 'mac' not in crypto:
        return False
    return True