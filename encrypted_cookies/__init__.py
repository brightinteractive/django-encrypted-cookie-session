# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import logging
import zlib

import django.contrib.sessions.backends.signed_cookies
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    # Django 1.5.x support
    from django.contrib.sessions.serializers import JSONSerializer
except ImportError:
    # Legacy Django support
    from django.core.signing import JSONSerializer
try:
    # Django 1.5.x support
    from django.contrib.sessions.serializers import PickleSerializer
except ImportError:
    # Legacy Django support
    from django.contrib.sessions.backends.signed_cookies import PickleSerializer
from django.core import signing

try:
    from django.utils.six.moves import cPickle as pickle
except ImportError:
    import pickle

from cryptography.fernet import InvalidToken

from encrypted_cookies import crypto

__version__ = '3.2.0'
log = logging.getLogger(__name__)


class BaseEncryptingSerializer(object):
    """
    Serialize/unserialize data with AES encryption using a secret key.
    """

    def dumps(self, obj):
        raw_data = self._serializer.dumps(obj)
        if getattr(settings, 'COMPRESS_ENCRYPTED_COOKIE', False):
            level = getattr(settings, 'ENCRYPTED_COOKIE_COMPRESSION_LEVEL', 6)
            raw_data = zlib.compress(raw_data, level)
        return crypto.encrypt(raw_data)

    def loads(self, data):
        decrypted_data = crypto.decrypt(data)
        if getattr(settings, 'COMPRESS_ENCRYPTED_COOKIE', False):
            try:
                decrypted_data = zlib.decompress(decrypted_data)
            except zlib.error as exc:
                # This probably means the server setting changed after a client
                # received the cookie. It should be fixed on the next request.
                log.warning('Could not decompress cookie value: %s: %s'
                            % (exc.__class__.__name__, exc))

        return self._serializer.loads(decrypted_data)

    def __getattr__(self, attr):
        return getattr(self._serializer, attr)


class EncryptingPickleSerializer(BaseEncryptingSerializer):

    def __init__(self):
        self._serializer = PickleSerializer()


class EncryptingJSONSerializer(BaseEncryptingSerializer):

    def __init__(self):
        self._serializer = JSONSerializer()


_DEFAULT_SERIALIZER = 'pickle'

def EncryptingSerializer():
    # use the default if unset, or set to any Falsey value
    serializer_setting = getattr(settings, 'ENCRYPTED_COOKIE_SERIALIZER',
                                 None) or _DEFAULT_SERIALIZER
    if serializer_setting == 'json':
        return EncryptingJSONSerializer()
    elif serializer_setting == 'pickle':
        return EncryptingPickleSerializer()
    else:
        raise ImproperlyConfigured("Invalid encrypted cookie serializer: '%s'"
                                   % serializer_setting)


class SessionStore(django.contrib.sessions.backends.signed_cookies.SessionStore):

    def load(self):
        """
        We load the data from the key itself instead of fetching from
        some external data store. Opposite of _get_session_key(),
        raises BadSignature if signature fails.
        """
        try:
            return signing.loads(self.session_key,
                # Create a signed cookie but with encrypted contents.
                serializer=EncryptingSerializer,
                max_age=settings.SESSION_COOKIE_AGE,
                salt='encrypted_cookies')
        except (signing.BadSignature, pickle.UnpicklingError,
                InvalidToken, ValueError) as exc:
            log.debug('recreating session because of exception: %s: %s'
                      % (exc.__class__.__name__, exc))
            self.create()
        return {}

    def _get_session_key(self):
        """
        Most session backends don't need to override this method, but we do,
        because instead of generating a random string, we want to actually
        generate a secure url-safe Base64-encoded string of data as our
        session key.
        """
        session_cache = getattr(self, '_session_cache', {})
        data = signing.dumps(session_cache, compress=True,
            salt='encrypted_cookies',
            serializer=EncryptingSerializer)

        cookie_size = len(data)
        log.debug('encrypted session cookie is %s bytes' % cookie_size)
        if cookie_size > 4093:
            # This will most definitely result in lost sessions.
            # http://browsercookielimits.squawky.net/
            log.error(
                'encrypted session cookie is too large for most browsers; '
                'size: %s' % cookie_size)

        return data
