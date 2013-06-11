# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.conf import settings

from m2secret import Secret


def encrypt(bytes):
    if not settings.SECRET_KEY:
        raise ValueError('The SECRET_KEY setting must not be empty.')

    secret = Secret()
    secret.encrypt(bytes, settings.SECRET_KEY)
    return secret.serialize()


def decrypt(encrypted_bytes):
    secret = Secret()
    secret.deserialize(encrypted_bytes)
    return secret.decrypt(settings.SECRET_KEY)
