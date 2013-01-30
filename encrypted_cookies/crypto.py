# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from Crypto.Cipher import AES
from django.conf import settings
import hashlib

def _cipher():
    # compute a 32-byte key
    key = hashlib.sha256(settings.SECRET_KEY).digest()
    assert len(key) == 32
    # compute a 16-byte IV
    IV = hashlib.md5(settings.SECRET_KEY).digest()
    assert len(IV) == 16

    # create an AES cipher, use CFB mode so we don't have to worry about padding
    cipher = AES.new(key, AES.MODE_CFB, IV)
    return cipher


def encrypt(bytes):
    if not settings.SECRET_KEY:
        raise ValueError('The SECRET_KEY setting must not be empty.')

    cipher = _cipher()
    return cipher.encrypt(bytes)


def decrypt(encrypted_bytes):
    cipher = _cipher()
    return cipher.decrypt(encrypted_bytes)
