# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import hashlib
import sys
import traceback

from django.conf import settings

# Use M2Crypto or pycrypto, whichever we find first.
m2c_exc = None
use_m2crypto = False
try:
    from m2secret import Secret
    use_m2crypto = True
except ImportError:
    m2c_exc = sys.exc_info()

pyc_exc = None
use_pycrypto = False
try:
    from Crypto.Cipher import AES
    use_pycrypto = True
except ImportError:
    pyc_exc = sys.exc_info()

if not use_pycrypto and not use_m2crypto:
    traceback.print_exception(*m2c_exc)
    traceback.print_exception(*pyc_exc)
    raise ImportError('there was a problem importing either m2secret, '
                      'M2Crypto, or pycrypto')


if not getattr(settings, 'ENCRYPTED_COOKIE_KEY', None):
    settings.ENCRYPTED_COOKIE_KEY = settings.SECRET_KEY


def pycrypto_cipher():
    # compute a 32-byte key
    key = hashlib.sha256(settings.ENCRYPTED_COOKIE_KEY).digest()
    assert len(key) == 32
    # compute a 16-byte IV
    IV = hashlib.md5(settings.ENCRYPTED_COOKIE_KEY).digest()
    assert len(IV) == 16

    # create an AES cipher, use CFB mode so we don't have to worry about
    # padding
    cipher = AES.new(key, AES.MODE_CFB, IV)
    return cipher


def encrypt(bytes):
    if not settings.ENCRYPTED_COOKIE_KEY:
        raise ValueError('The ENCRYPTED_COOKIE_KEY setting must not be empty.')

    if use_m2crypto:
        secret = Secret()
        secret.encrypt(bytes, settings.ENCRYPTED_COOKIE_KEY)
        return secret.serialize()
    else:
        cipher = pycrypto_cipher()
        return cipher.encrypt(bytes)


def decrypt(encrypted_bytes):
    if use_m2crypto:
        secret = Secret()
        secret.deserialize(encrypted_bytes)
        return secret.decrypt(settings.ENCRYPTED_COOKIE_KEY)
    else:
        cipher = pycrypto_cipher()
        return cipher.decrypt(encrypted_bytes)
