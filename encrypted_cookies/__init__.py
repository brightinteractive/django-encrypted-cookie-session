# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.conf import settings
from django.core import signing
from django.contrib.sessions.backends.signed_cookies import PickleSerializer
from encrypted_cookies import crypto
import django.contrib.sessions.backends.signed_cookies

__version__ = '1.0.0'


class EncryptingPickleSerializer(PickleSerializer):
    def dumps(self, obj):
        return crypto.encrypt(super(EncryptingPickleSerializer, self).dumps(obj))

    def loads(self, data):
        decrypted_data = crypto.decrypt(data)
        return super(EncryptingPickleSerializer, self).loads(decrypted_data)


class SessionStore(django.contrib.sessions.backends.signed_cookies.SessionStore):

    def load(self):
        """
        We load the data from the key itself instead of fetching from
        some external data store. Opposite of _get_session_key(),
        raises BadSignature if signature fails.
        """
        try:
            return signing.loads(self.session_key,
                serializer=EncryptingPickleSerializer,
                max_age=settings.SESSION_COOKIE_AGE,
                salt='encrypted_cookies')
        except (signing.BadSignature, ValueError):
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
        return signing.dumps(session_cache, compress=True,
            salt='encrypted_cookies',
            serializer=EncryptingPickleSerializer)
