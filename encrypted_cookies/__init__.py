# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.conf import settings
from django.core import signing
import django.contrib.sessions.backends.signed_cookies
from django.contrib.sessions.backends.signed_cookies import PickleSerializer

from encrypted_cookies import crypto
import django_paranoia.sessions
import m2secret

__version__ = '1.1.0'


class EncryptingPickleSerializer(PickleSerializer):
    """
    Serialize/unserialize data with AES encryption using a secret key.
    """

    def dumps(self, obj):
        raw_data = super(EncryptingPickleSerializer, self).dumps(obj)
        return crypto.encrypt(raw_data)

    def loads(self, data):
        decrypted_data = crypto.decrypt(data)
        return super(EncryptingPickleSerializer, self).loads(decrypted_data)


class SessionStore(
        django.contrib.sessions.backends.signed_cookies.SessionStore,
        django_paranoia.sessions.SessionStore):

    def load(self):
        """
        We load the data from the key itself instead of fetching from
        some external data store. Opposite of _get_session_key(),
        raises BadSignature if signature fails.
        """
        try:
            return signing.loads(self.session_key,
                # Create a signed cookie but with encrypted contents.
                serializer=EncryptingPickleSerializer,
                max_age=settings.SESSION_COOKIE_AGE,
                salt='encrypted_cookies')
        except (signing.BadSignature, m2secret.DecryptionError, ValueError):
            self.create()
        return {}

    def save(self, must_create=False):
        # Run django_paranoia pre-save logic.
        self.prepare_data(must_create=must_create)
        # Run the actual save logic from signed cookies.
        return super(SessionStore, self).save(must_create=must_create)

    def _get_session_key(self):
        """
        Most session backends don't need to override this method, but we do,
        because instead of generating a random string, we want to actually
        generate a secure url-safe Base64-encoded string of data as our
        session key.
        """
        session_cache = getattr(self, '_session_cache', {})
        return signing.dumps(session_cache, compress=True,
            salt='encrypted_cookies',
            serializer=EncryptingPickleSerializer)
