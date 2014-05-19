# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.conf import settings
from m2secret import Secret


def encrypted_cookie_key():
    key = getattr(settings, 'ENCRYPTED_COOKIE_KEY', None)
    if not key:
        key = settings.SECRET_KEY
    return key


def encrypt(plaintext_bytes):
    key = encrypted_cookie_key()
    if not key:
        raise ValueError('The ENCRYPTED_COOKIE_KEY and SECRET_KEY settings must not both be empty.')

    secret = Secret()
    secret.encrypt(plaintext_bytes, key)
    return secret.serialize()


def decrypt(encrypted_bytes):
    secret = Secret()
    secret.deserialize(encrypted_bytes)
    return secret.decrypt(encrypted_cookie_key())
