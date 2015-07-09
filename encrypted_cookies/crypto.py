# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import logging
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

log = logging.getLogger(__name__)


def encrypt(plaintext_bytes):
    """
    Returns an ecnrypted version of plaintext_bytes.

    The encrypted value is a URL-encoded base 64 value.
    """
    return get_backend().encrypt(plaintext_bytes)


def decrypt(encrypted_bytes):
    """
    Returns a decrypted version of encrypted_bytes.
    """
    return get_backend().decrypt(encrypted_bytes)


class DecryptionError(Exception):
    """
    An error while decrypting data such as a malformed token.
    """


default_backend = 'cryptography'
backend_lookup = {}


def get_backend():
    module_name = (getattr(settings, 'ENCRYPTED_COOKIE_BACKEND', None) or
                   default_backend)
    Backend = backend_lookup.get(module_name, None)
    if not Backend:
        raise ImproperlyConfigured(
            'No backend exists for module named "%s"; possible backends: %s'
            % (module_name, repr(backend_lookup.keys())))

    return Backend()


def register_backend(cls):
    backend_lookup[cls.module_name] = cls
    return cls


class EncryptedCookieBackend(object):
    module_name = None

    def __init__(self):
        self.keys = self.get_keys()
        if not len(self.keys):
            raise ImproperlyConfigured(
                '%s: The ENCRYPTED_COOKIE_KEYS setting cannot be empty.'
                % self.__class__.__name__)

    def get_keys(self):
        return list(getattr(settings, 'ENCRYPTED_COOKIE_KEYS', None) or [])

    def encrypt(self, plaintext_bytes):
        raise NotImplementedError

    def decrypt(self, encrypted_bytes):
        raise NotImplementedError


@register_backend
class CryptographyBackend(EncryptedCookieBackend):
    module_name = 'cryptography'

    def __init__(self):
        super(CryptographyBackend, self).__init__()
        from cryptography.fernet import Fernet, MultiFernet
        self.fernet = MultiFernet([Fernet(k) for k in self.keys])

    def encrypt(self, plaintext_bytes):
        return self.fernet.encrypt(plaintext_bytes)

    def decrypt(self, encrypted_bytes):
        from cryptography.fernet import InvalidToken
        try:
            return self.fernet.decrypt(encrypted_bytes)
        except InvalidToken:
            exc_type, exc_value, tb = sys.exc_info()
            new_exc = DecryptionError('%s: %s' % (exc_type.__name__, exc_value))
            raise new_exc, None, tb


@register_backend
class M2CryptoBackend(EncryptedCookieBackend):
    module_name = 'M2Crypto'

    def __init__(self):
        super(M2CryptoBackend, self).__init__()
        from m2secret import Secret

        if len(self.keys) > 1:
            raise NotImplementedError(
                '%s: cannot define more than one key; rotation not implemented'
                % self.__class__.__name__)

        self.key = self.keys[0]

        self.secret = Secret()

    def get_keys(self):
        keys = super(M2CryptoBackend, self).get_keys()

        if not len(keys):
            old_key = getattr(settings, 'ENCRYPTED_COOKIE_KEY', None)
            if old_key:
                log.warning('The ENCRYPTED_COOKIE_KEY setting is deprecated; '
                            'define ENCRYPTED_COOKIE_KEYS=[...] instead.')
                keys.append(old_key)

        if not len(keys):
            django_key = getattr(settings, 'SECRET_KEY', '')
            if django_key:
                log.warning('Falling back to the SECRET_KEY setting is deprecated; '
                            'define ENCRYPTED_COOKIE_KEYS=[...] instead.')
                keys.append(django_key)

        return keys

    def encrypt(self, plaintext_bytes):
        self.secret.encrypt(plaintext_bytes, self.key)
        return self.secret.serialize()

    def decrypt(self, encrypted_bytes):
        import m2secret
        try:
            self.secret.deserialize(encrypted_bytes)
            return self.secret.decrypt(self.key)
        except m2secret.DecryptionError:
            exc_type, exc_value, tb = sys.exc_info()
            new_exc = DecryptionError('%s: %s' % (exc_type.__name__, exc_value))
            raise new_exc, None, tb
