# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import warnings

from django.conf import settings

from m2secret import Secret

if not getattr(settings, 'ENCRYPTED_COOKIE_KEY', None):
    warnings.warn('You must set ENCRYPTED_COOKIE_KEY; '
                  'falling back to SECRET_KEY', DeprecationWarning)
    settings.ENCRYPTED_COOKIE_KEY = settings.SECRET_KEY


def encrypt(bytes):
    if not settings.ENCRYPTED_COOKIE_KEY:
        raise ValueError('The ENCRYPTED_COOKIE_KEY setting must not be empty.')

    secret = Secret()
    secret.encrypt(bytes, settings.ENCRYPTED_COOKIE_KEY)
    return secret.serialize()


def decrypt(encrypted_bytes):
    secret = Secret()
    secret.deserialize(encrypted_bytes)
    return secret.decrypt(settings.ENCRYPTED_COOKIE_KEY)
