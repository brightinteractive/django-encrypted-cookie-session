# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.core import signing
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.unittest.case import skipUnless

import mock

from encrypted_cookies import get_paranoid
from encrypted_cookies import EncryptingPickleSerializer, SessionStore


class EncryptionTests(TestCase):

    def setUp(self):
        self.pkl = EncryptingPickleSerializer()

    @override_settings(SECRET_KEY='', ENCRYPTED_COOKIE_KEY='')
    def test_empty_secret_key_not_allowed(self):
        with self.assertRaises(ValueError):
            self.pkl.dumps('summat')

    def test_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted)
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    def test_multiple_encrypt_decrypt(self):
        """
        Make sure that crypto isn't invalidly reusing a same cipher object
        in a feedback mode (this test was for the pycrypto implementation)
        """
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.pkl.dumps('asdf')
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    @override_settings(COMPRESS_ENCRYPTED_COOKIE=True)
    def test_compressed_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted)
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    def test_recover_from_uncompressed_value(self):
        plaintext_bytes = 'adsfasdfw34wras'
        with override_settings(COMPRESS_ENCRYPTED_COOKIE=False):
            encrypted = self.pkl.dumps(plaintext_bytes)
        with override_settings(COMPRESS_ENCRYPTED_COOKIE=True):
            # Make sure this doesn't raise an exception.
            decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)


class SessionStoreTests(TestCase):

    def setUp(self):
        req = RequestFactory().get('/')
        req.META['REMOTE_ADDR'] = '10.0.0.1'
        if get_paranoid:
            self.sess = SessionStore(request_meta=req.META.copy())
        else:
            self.sess = SessionStore()

    def test_save_load(self):
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        self.assertEqual(stor['secret'], 'laser beams')

    def test_wrong_key(self):
        with self.settings(ENCRYPTED_COOKIE_KEY='the first key'):
            self.sess['secret'] = 'laser beams'
            self.sess.save()
        with self.settings(ENCRYPTED_COOKIE_KEY='the second key'):
            stor = self.sess.load()
        # The DecryptionError is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    @mock.patch('encrypted_cookies.signing.loads')
    def test_bad_signature(self, loader):
        loader.side_effect = signing.BadSignature
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        # The BadSignature error is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    @mock.patch('encrypted_cookies.signing.loads')
    def test_bad_signing_value(self, loader):
        loader.side_effect = ValueError
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        # The ValueError is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    @mock.patch('encrypted_cookies.EncryptingPickleSerializer')
    def test_use_encrypted_pickles(self, PicklerClass):
        pickler = mock.Mock()
        PicklerClass.return_value = pickler
        pickler.dumps.return_value = '<data>'

        self.sess.save()
        self.sess.load()

        # Because there is multiple inheritance going on now, make
        # sure that the encrypted pickler is used.
        assert pickler.dumps.called
        assert pickler.loads.called

    @skipUnless(get_paranoid, 'django_paranoia not installed')
    def test_cache_key(self):
        ck = self.sess.cache_key
        assert ck.startswith('django_paranoid'), (
            'Unexpected cache key: %s' % ck)

    @skipUnless(get_paranoid, 'django_paranoia not installed')
    def test_paranoia_catches_tampering(self):
        req = RequestFactory().get('/')
        req.META['REMOTE_ADDR'] = '192.168.1.1'  # alter this value.
        with mock.patch('django_paranoia.sessions.warning.send') as warn:
            self.sess.save()
            self.sess.check_request_data(request=req)
        assert warn.called
