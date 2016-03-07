# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cryptography import fernet


def encrypt(plaintext_bytes):
    """
    Returns an encrypted version of plaintext_bytes.

    The encrypted value is a URL-encoded base 64 value.
    """
    return configure_fernet().encrypt(plaintext_bytes)


def decrypt(encrypted_bytes):
    """
    Returns a decrypted version of encrypted_bytes.
    """
    return configure_fernet().decrypt(encrypted_bytes)


def configure_fernet():
    keys = list(getattr(settings, 'ENCRYPTED_COOKIE_KEYS', None) or [])
    if not len(keys):
        raise ImproperlyConfigured(
            'The ENCRYPTED_COOKIE_KEYS settings cannot be empty.')

    return fernet.MultiFernet([fernet.Fernet(k) for k in keys])
